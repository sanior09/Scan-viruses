rule Malicious_PowerShell {
    meta:
        description = "Detects obfuscated and malicious PowerShell commands"
        author = "J.A.R.V.I.S."
    strings:
        $ps1 = "ExecutionPolicy Bypass" nocase
        $ps2 = "Hidden -Command" nocase
        $ps3 = "Invoke-WebRequest" nocase
        $ps4 = "Net.WebClient" nocase
        $ps5 = "DownloadString" nocase
        $ps6 = "eval(base64_decode" nocase
        $obf1 = "-enc " nocase
        $obf2 = "-EncodedCommand" nocase
    condition:
        3 of ($ps*) or (1 of ($obf*) and 1 of ($ps*))
}

rule Suspicious_VBS_Payload {
    meta:
        description = "Detects VBScript dropping or executing shell payloads"
        author = "J.A.R.V.I.S."
    strings:
        $vbs_obj1 = "CreateObject(\"WScript.Shell\")" nocase
        $vbs_obj2 = "CreateObject(\"Scripting.FileSystemObject\")" nocase
        $vbs_drop = ".Run" nocase
        $vbs_exec = "powershell" nocase
        $vbs_cmd = "cmd.exe /c" nocase
    condition:
        uint16(0) != 0x5A4D and (1 of ($vbs_obj*)) and ($vbs_drop or $vbs_exec or $vbs_cmd)
}

rule Malicious_Office_Macro {
    meta:
        description = "Detects Office Macro executing suspicious commands"
        author = "J.A.R.V.I.S."
    strings:
        $macro1 = "AutoOpen" nocase
        $macro2 = "Document_Open" nocase
        $macro3 = "Workbook_Open" nocase
        $exec1 = "WScript.Shell" nocase
        $exec2 = "powershell" nocase
        $exec3 = "cmd.exe" nocase
        $exec4 = "certutil" nocase
    condition:
        uint16(0) != 0x5A4D and (1 of ($macro*)) and (1 of ($exec*))
}
