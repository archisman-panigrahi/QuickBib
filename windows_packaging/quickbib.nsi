; NSIS script to package the PyInstaller 'dist/QuickBib' output into an installer.
; This script assumes the build step produces a folder 'dist\QuickBib' with QuickBib.exe

!define APP_NAME "QuickBib"
!define COMPANY "Archisman Panigrahi"
!define VERSION "0.8.1"

; Installer display name shown in the window title and installer UI
Name "${APP_NAME}"

; Default execution level: user (no UAC unless needed)
RequestExecutionLevel user

!include nsDialogs.nsh
!include LogicLib.nsh
!include FileFunc.nsh

; Use Modern UI 2 so we can set the installer UI icon to the application icon
!define MUI_ICON "..\\assets\\icon\\64x64\\io.github.archisman_panigrahi.QuickBib.ico"
!include MUI2.nsh

Var INSTALL_SCOPE

; The NSIS script lives in the `windows_packaging` directory. Paths in this script
; are resolved relative to the script's location, so reference files in the repo root
; using a parent-directory prefix.
Icon "..\\assets\\icon\\64x64\\io.github.archisman_panigrahi.QuickBib.ico"

OutFile "${APP_NAME}-Installer-${VERSION}.exe"
InstallDir "$LOCALAPPDATA\\Programs\\${APP_NAME}"

Page directory
Page instfiles

SetCompress off

Function .onInit
  ; Force per-user install and context
  StrCpy $INSTALL_SCOPE "USER"
  StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"
  SetShellVarContext current
FunctionEnd



Section "Install"

  ; Debug: Log the install scope and directory
  DetailPrint "INSTALL_SCOPE: $INSTALL_SCOPE"
  DetailPrint "INSTDIR (before): $INSTDIR"

  ; Force per-user install dir and context
  StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\${APP_NAME}"
  SetShellVarContext current

  DetailPrint "INSTDIR (after): $INSTDIR"
  DetailPrint "Starting file copy..."

  SetOutPath "$INSTDIR"

  ; Copy all files from the PyInstaller output (dist is at repo root, so step up one dir)
  File /r "..\\dist\\QuickBib\\*"
  DetailPrint "File copy completed"

  ; Include repository LICENSE in the installed files so users can view the license
  File /oname=LICENSE "..\\LICENSE"

  ; Create Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\QuickBib.exe"

  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\QuickBib.exe"

  ; Write install location for uninstaller (per-user)
  WriteRegStr HKCU "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir" "$INSTDIR"

  ; Register uninstall info so it appears in Add/Remove Programs (per-user)
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${COMPANY}"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayIcon" "$INSTDIR\\QuickBib.exe"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\Uninstall.exe"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "QuietUninstallString" "$INSTDIR\\Uninstall.exe /S"

  ; Write Uninstaller
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
  ; Read install dir from per-user registry
  ReadRegStr $0 HKCU "Software\\${COMPANY}\\${APP_NAME}" "Install_Dir"
  StrCmp $0 "" 0 +2
    Goto done

  ; Remove shortcuts
  Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\\${APP_NAME}"
  Delete "$DESKTOP\\${APP_NAME}.lnk"

  ; Delete files
  RMDir /r "$0"

  ; Remove per-user registry
  DeleteRegKey HKCU "Software\\${COMPANY}\\${APP_NAME}"
  DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"

done:
  Delete "$0\\Uninstall.exe"
SectionEnd

