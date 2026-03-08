rule WannaCry
{
    meta:
        description = "Detects WannaCry Ransomware strings/mutex"
        author = "Ransomware Defense System"
        date = "2026-02-21"
    strings:
        $s1 = "WNcry@2ol7" wide ascii
        $s2 = "tasksche.exe" wide ascii
        $s3 = "msg/m_korean.wnry" wide ascii
        $s4 = "msg/m_arabic.wnry" wide ascii
        $s5 = "wanadecryptor" nocase wide ascii
        $mz = { 4D 5A }
    condition:
        $mz at 0 and 2 of ($s*)
}

rule Petya_NotPetya
{
    meta:
        description = "Detects Petya/NotPetya Ransomware components"
        author = "Ransomware Defense System"
    strings:
        $s1 = "dllhost.dat" wide ascii
        $s2 = "wevtutil cl Setup" wide ascii
        $s3 = "fsutil usn deletejournal" wide ascii
        $s4 = "cipher.exe /C" wide ascii
        $s5 = "schtasks /Create /SC once /TN" wide ascii
        $mz = { 4D 5A }
    condition:
        $mz at 0 and 2 of ($s*)
}

rule LockBit
{
    meta:
        description = "Detects LockBit Ransomware common strings"
        author = "Ransomware Defense System"
    strings:
        $s1 = "LockBit" wide ascii
        $s2 = "Restore-My-Files.txt" wide ascii
        $s3 = "SOFTWARE\\LockBit" wide ascii
        $s4 = "vssadmin delete shadows /all /quiet" wide ascii
    condition:
        3 of ($s*)
}

rule Generic_Ransomware_Behavior
{
    meta:
        description = "Detects generic ransomware destructive behaviors"
        author = "Ransomware Defense System"
    strings:
        $cmd1 = "vssadmin.exe Delete Shadows /All /Quiet" nocase wide ascii
        $cmd2 = "wbadmin DELETE SYSTEMSTATEBACKUP" nocase wide ascii
        $cmd3 = "wbadmin DELETE SYSTEMSTATEBACKUP -keepVersions:0" nocase wide ascii
        $cmd4 = "bcdedit /set {default} recoveryenabled No" nocase wide ascii
        $cmd5 = "bcdedit /set {default} bootstatuspolicy ignoreallfailures" nocase wide ascii
    condition:
        any of ($cmd*)
}
