WINDOWS_FAKE_STORE = r"""
param([string]$Mode, [string]$Payload)
Add-Type -TypeDefinition @'
using System;
using System.Security.Cryptography.X509Certificates;
public class FakeCert { public byte[] RawData = new byte[] { 1, 2, 3 }; }
public class FakeStore {
    public static bool present = true;
    public static bool failMachine = false;
    public static bool failAdd = false;
    public static bool userOnly = false;
    public static bool caOnly = false;
    private string name;
    private string location;
    public FakeStore(string n, string l) { name = n; location = l; }
    public FakeCert[] Certificates { get {
        return name == (caOnly ? "CA" : "Root") && present && (!userOnly || location == "CurrentUser") ? new FakeCert[] { new FakeCert() } : new FakeCert[0];
    } }
    public void Open(OpenFlags flags) { }
    public void Close() { }
    public void Add(FakeCert cert) {
        if (failAdd) throw new UnauthorizedAccessException("fake disallowed add failure");
    }
    public void Remove(FakeCert cert) {
        if (location == "CurrentUser" || failMachine) throw new UnauthorizedAccessException();
        present = false;
    }
}
'@
if ($Mode -eq 'remain') { [FakeStore]::failMachine = $true }
if ($Mode -eq 'add-failure') { [FakeStore]::failAdd = $true }
if ($Mode -eq 'user-only') { [FakeStore]::userOnly = $true }
if ($Mode -eq 'ca-only') { [FakeStore]::caOnly = $true }
$hash = [System.Security.Cryptography.SHA256]::Create()
try { $env:KADOKA_BLOCKED_ROOTS = ([BitConverter]::ToString($hash.ComputeHash([byte[]](1,2,3)))).Replace('-', '').ToLowerInvariant() }
finally { $hash.Dispose() }
$source = Get-Content -Raw -LiteralPath $Payload
$source = $source.Replace('[System.Security.Cryptography.X509Certificates.X509Store]', '[FakeStore]')
Invoke-Expression $source
"""
