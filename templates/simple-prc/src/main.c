#ifdef PALMDEV_LEGACY_SDK
#define PILOT_PRECOMPILED_HEADERS_OFF
#include <Pilot.h>
#else
#include <PalmOS.h>
#endif
#ifdef PALMDEV_LEGACY_SDK
DWord PilotMain(Word cmd, Ptr p, Word flags) { (void)p; (void)flags; return cmd == sysAppLaunchCmdNormalLaunch ? 0 : 0; }
#else
UInt32 PilotMain(UInt16 cmd, void *p, UInt16 flags) { (void)p; (void)flags; return cmd == sysAppLaunchCmdNormalLaunch ? 0 : 0; }
#endif
