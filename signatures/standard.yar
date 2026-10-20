rule EICAR_Test_File {
    meta:
        description = "Standard EICAR Anti-Virus Test File"
        author = "J.A.R.V.I.S."
    strings:
        $s1 = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        $s2 = "X5O!P%@AP[4\\\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    condition:
        $s1 or $s2
}

rule Suspicious_Process_Injection {
    meta:
        description = "Detects explicit process injection patterns"
        author = "J.A.R.V.I.S."
    strings:
        $api1 = "VirtualAllocEx" ascii wide
        $api2 = "WriteProcessMemory" ascii wide
        $api3 = "CreateRemoteThread" ascii wide
        $api4 = "NtUnmapViewOfSection" ascii wide
        $api5 = "QueueUserAPC" ascii wide
    condition:
        // Must have at least 3 indicators including remote alloc & write
        ($api1 and $api2 and ($api3 or $api4 or $api5)) or (4 of ($api*))
}
