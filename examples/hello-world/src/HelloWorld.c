#ifdef PALMDEV_LEGACY_SDK
#define PILOT_PRECOMPILED_HEADERS_OFF
#include <Pilot.h>
#else
#include <PalmOS.h>
#endif

#define MainForm 1000

static Boolean AppHandleEvent(EventType *event) {
    if (event->eType == frmLoadEvent) {
        FormType *form = FrmInitForm(event->data.frmLoad.formID);
        FrmSetActiveForm(form);
        return true;
    }
    if (event->eType == frmOpenEvent) {
        FormType *form = FrmGetActiveForm();
        FrmDrawForm(form);
        WinDrawChars("Hello, World!", 13, 42, 72);
        return true;
    }
    return false;
}

#ifdef PALMDEV_LEGACY_SDK
DWord PilotMain(Word cmd, Ptr cmdPBP, Word launchFlags) {
#else
UInt32 PilotMain(UInt16 cmd, void *cmdPBP, UInt16 launchFlags) {
#endif
    EventType event;
#ifdef PALMDEV_LEGACY_SDK
    Word menuError;
#else
    UInt16 menuError;
#endif
    (void)cmdPBP; (void)launchFlags;
    if (cmd != sysAppLaunchCmdNormalLaunch) return 0;
    FrmGotoForm(MainForm);
    do {
        EvtGetEvent(&event, evtWaitForever);
        if (!SysHandleEvent(&event) && !MenuHandleEvent(0, &event, &menuError)
            && !AppHandleEvent(&event))
            FrmDispatchEvent(&event);
    } while (event.eType != appStopEvent);
    FrmCloseAllForms();
    return 0;
}
