!define APPNAME "CodeGra.fs"
!define REGUINSTKEY "{58c6e5ab-979c-40b5-b78c-05e20c7e2067}" ; You could use APPNAME here but a GUID is guaranteed to be unique. Use guidgen.com to create your own.
!define REGUINST 'HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${REGUINSTKEY}"'
Name "${APPNAME}"
Outfile "setup.exe"
RequestExecutionLevel Admin
Unicode True
InstallDir "$ProgramFiles32\${APPNAME}"
InstallDirRegKey ${REGUINST} UninstallString


!define MUI_COMPONENTSPAGE_NODESC
!include MUI2.nsh
!include LogicLib.nsh
!include Sections.nsh
!include EnvVarUpdate.nsh

!define MUI_ICON "static/ms-icon.ico"
!define MUI_UNICON "static/ms-icon.ico"

Var SMDir ; Start menu folder


Function .onInit
UserInfo::GetAccountType
Pop $0
${If} $0 != "admin" ; Require admin rights on WinNT4+
	MessageBox MB_IconStop "Administrator rights required!"
	SetErrorLevel 740 ; ERROR_ELEVATION_REQUIRED
	Quit
${EndIf}
FunctionEnd


!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE ".\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_STARTMENU 0 $SMDir
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE English


Section "-Required files"
AddSize 35
SectionIn RO
SetOutPath $InstDir
WriteUninstaller "$InstDir\Uninstall.exe"
WriteRegStr ${REGUINST} UninstallString '"$InstDir\Uninstall.exe"'
WriteRegStr ${REGUINST} DisplayName "${APPNAME}"
WriteRegStr ${REGUINST} UrlInfoAbout "http://github.com/CodeGra-de/CodeGra.fs"
WriteRegStr ${REGUINST} DisplayIcon "$InstDir\cgfs-qt.exe,0"
SectionEnd

Section "Gui" SID_A1
File "/oname=$InstDir\cgfs-qt.exe" ".\dist\gui.exe"
SectionEnd

Section "Api consumer" SID_A2
CreateDirectory "$InstDir\cgapi-consumer\"
SetOutPath "$InstDir\cgapi-consumer\"
File ".\dist\cgapi-consumer\*"
;; File "/oname=$InstDir\cgapi-consumer.exe" ".\dist\api_consumer.exe"
SectionEnd

Section "Start menu shortcuts"
!insertmacro MUI_STARTMENU_WRITE_BEGIN 0
CreateDirectory "$SMPrograms\$SMDir"
${If} ${SectionIsSelected} ${SID_A1}
	CreateShortcut /NoWorkingDir "$SMPrograms\$SMDir\cgfs-qt.lnk" '"$InstDir\cgfs-qt.exe"'
${EndIf}

WriteRegStr ${REGUINST} "NSIS:SMDir" $SMDir ; We need to save the start menu folder so we can remove the shortcuts in the uninstaller
!insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section "Add env vars" SID_A3
${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$InstDir\cgapi-consumer\"
SectionEnd


Section -Uninstall
ReadRegStr $SMDir ${REGUINST} "NSIS:SMDir"
${If} $SMDir != ""
	Delete "$SMPrograms\$SMDir\cgfs-qt.lnk"
	RMDir "$SMPrograms\$SMDir"
${EndIf}

${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$InstDir\cgapi-consumer\"

Delete "$InstDir\cgfs-qt.exe"
Delete "$InstDir\cgapi-consumer\*"
RMDir "$InstDir\cgapi-consumer\"
Delete "$InstDir\uninstall.exe"
RMDir "$InstDir"
DeleteRegKey ${REGUINST}
SectionEnd


Function .onSelChange
StrCpy $0 1
SectionGetFlags ${SID_A1} $1
IntOp $0 $0 & $1
SectionGetFlags ${SID_A2} $1
IntOp $0 $0 & $1
SectionGetFlags ${SID_A3} $1
IntOp $0 $0 & $1
IntOp $0 $0 & ${SF_SELECTED} ; Only enable next button when gui, api_consumer and path are being installed

!if "${MUI_SYSVERSION}" >= 2.0
StrCpy $1 $mui.Button.Next
!else
GetDlgItem $1 $hwndParent 1 ; Next button
!endif
EnableWindow $1 $0
FunctionEnd