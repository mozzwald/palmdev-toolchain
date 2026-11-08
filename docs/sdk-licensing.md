# SDK licensing

The installer only installs an SDK after it finds and displays license/EULA files inside that SDK's pinned source directory and the developer types `agree`. It stores source revision, license hash, and timestamp locally. Declining leaves no installed SDK files.

Every selected SDK has its own response, including Handspring. There is no environment variable or global switch that accepts all licenses. Empty, binary, or obviously malformed agreement files are rejected; these checks identify readable agreement documents, not their legal applicability. All matching included agreements are presented. Press `q` to leave each `less` license viewer and return to the acceptance prompt.

At the current lock, every discovered `sdk-*` directory has an included agreement, including SDKs 3.5, 4, and 5r4. The missing-license guard remains intentional: a future SDK without an identifiable agreement is skipped rather than inferred from another version's agreement.
