#!/usr/bin/env bash
set -euo pipefail
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"
repo=${PALMDEV_SDK_REPO:-$PALM_OS_SDK_REPO}; rev=${PALMDEV_SDK_REV:-$PALM_OS_SDK_REV}; requested=${PALMDEV_SDK_SELECTION:-}
require_python
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM
git clone --no-checkout "$repo" "$tmp/source" >/dev/null
git -C "$tmp/source" checkout --detach "$rev" >/dev/null
sdks=()
while IFS= read -r v; do sdks+=("$v"); done < <(git -C "$tmp/source" ls-tree -d --name-only "$rev" | sed -n 's#^sdk-##p' | sort)
[ "${#sdks[@]}" -gt 0 ] || { echo "No sdk-* directories found at $repo@$rev" >&2; exit 1; }

select_sdks_interactively() {
  # Pure Bash on purpose: macOS ships Bash 3.2, and seven SDKs do not justify
  # a curses dependency. Arrow keys and j/k both move the cursor.
  local cursor=0 key extra i v pointer checked status found
  # Fresh installs default to 3.1 and 3.5. On later setup runs, accepted
  # SDKs stay visible but start unselected and therefore are not revisited.
  chosen=()
  for v in 3.1 3.5; do
    [ -d "$(sdk_dir "$v")" ] || chosen+=("$v")
  done
  while :; do
    printf '\033[2J\033[H'
    echo 'Select Palm OS SDKs to install or repair'
    echo 'Space toggles [X]; Up/Down (or j/k) moves; Enter confirms; q cancels.'
    echo 'Status “installed” means the SDK is already local and starts unselected.'
    echo
    for i in "${!sdks[@]}"; do
      v=${sdks[$i]}; pointer=' '; [ "$i" -eq "$cursor" ] && pointer='>'
      checked=' '; found=0
      for selected in ${chosen[@]+"${chosen[@]}"}; do [ "$selected" = "$v" ] && found=1; done
      [ "$found" = 1 ] && checked=X
      status=''
      [ -d "$(sdk_dir "$v")" ] && status='installed'
      printf ' %s [%s] %-5s %s\n' "$pointer" "$checked" "$v" "$status"
    done
    printf '\nSelection: '
    # IFS= preserves a literal Space; without it Bash trims the key before
    # the case statement gets it.
    IFS= read -rsn1 key
    case "$key" in
      ' ')
        found=0; remaining=()
        for selected in ${chosen[@]+"${chosen[@]}"}; do
          if [ "$selected" = "${sdks[$cursor]}" ]; then found=1; else remaining+=("$selected"); fi
        done
        if [ "$found" = 1 ]; then chosen=(${remaining[@]+"${remaining[@]}"}); else chosen+=("${sdks[$cursor]}"); fi
        ;;
      j) [ "$cursor" -lt "$(( ${#sdks[@]} - 1 ))" ] && cursor=$((cursor + 1)) ;;
      k) [ "$cursor" -gt 0 ] && cursor=$((cursor - 1)) ;;
      ''|$'\n'|$'\r')
        if [ "${#chosen[@]}" -gt 0 ] || compgen -G "$LOCAL/sdk/sdk-*" >/dev/null; then break; fi
        printf '\nChoose at least one SDK. Press any key to continue.'; read -rsn1 _
        ;;
      q|Q) chosen=(); break ;;
      $'\033')
        read -rsn2 -t 1 extra || true
        case "$extra" in '[A') [ "$cursor" -gt 0 ] && cursor=$((cursor - 1)) ;; '[B') [ "$cursor" -lt "$(( ${#sdks[@]} - 1 ))" ] && cursor=$((cursor + 1)) ;; esac
        ;;
    esac
  done
  printf '\033[2J\033[H'
}

if [ -z "$requested" ]; then
  if is_tty; then
    select_sdks_interactively
    [ "${#chosen[@]}" -gt 0 ] || { echo 'No additional SDKs selected.'; exit 0; }
    requested="${chosen[*]}"
  else
    requested='3.1 3.5'
  fi
fi
unknown=0
for choice in $requested; do
  # Selections are SDK versions, never indexes into the discovered list.
  v=$choice
  [[ " ${sdks[*]} " == *" $v "* ]] || { echo "Unknown SDK: $choice" >&2; unknown=1; continue; }
  dest=$(sdk_dir "$v"); meta="$LOCAL/licenses/sdk-$v.accepted"
  if python3 "$ROOT/scripts/sdk-state.py" install "$dest" "$meta" "$rev" "$tmp/source/sdk-$v" "Palm OS SDK $v"; then :; else
    status=$?
    case "$status" in 3|4) ;; *) exit "$status" ;; esac
  fi
  # A declined SDK is removed from the working tree immediately; the complete
  # temporary clone, including Git objects, is always removed on exit.
  rm -rf "$tmp/source/sdk-$v"
done
exit "$unknown"
