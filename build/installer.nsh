!include EnvVarUpdate.nsh
 
!macro customInstall
  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$InstDir\"
  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$InstDir\cgapi-consumer\"
!macroend
 
!macro customUnInstall
  ${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$InstDir\"
  ${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$InstDir\cgapi-consumer\"
!macroend
