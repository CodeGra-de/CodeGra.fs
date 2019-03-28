!include EnvVarUpdate.nsh
!include VersionCompare.nsh
 
!macro customInstall
  ReadRegStr $R0 HKLM "SOFTWARE\Classes\Installer\Dependencies\WinFsp" "Version"
  StrCmp $R0 "" installWinFsp 0

  ${VersionCompare} $R0 "1.4.18344" $R0
  IntCmp $R0 2 0 afterInstallWinFsp

  installWinFsp:
  ExecWait '"msiexec" /i "$INSTDIR\winfsp.msi"'

  ReadRegStr $R0 HKLM "SOFTWARE\Classes\Installer\Dependencies\WinFsp" "Version"
  StrCmp $R0 "" 0 afterInstallWinFsp
  
  MessageBox MB_OK "WinFsp installation failed! Please make sure it succeeds before using CodeGrade Filesystem! $INSTDIR\Uninstall CodeGrade Filesystem.exe"
  ExecWait "$INSTDIR\Uninstall CodeGrade Filesystem.exe"
  Quit

  afterInstallWinFsp:
  Delete "$INSTDIR\winfsp.msi"

  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$InstDir\"
  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$InstDir\cgapi-consumer\"
!macroend
 
!macro customUnInstall
  ${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$InstDir\"
  ${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$InstDir\cgapi-consumer\"
!macroend
