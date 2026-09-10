; Inno Setup script for the Book Shelf Windows installer.
; Compile with Inno Setup 6: place BookShelf.exe (the one-file build),
; BookShelf.ico and LICENSE.txt next to this file, open this script and
; press Compile. Output lands in the Output subfolder.

#define AppVersion "1.1.0"
#define AppName "Book Shelf"
#define AppPublisher "farukylmz0550"
#define AppURL "https://github.com/farukylmz0550/bookshelf-desktop"
#define AppExe "BookShelf.exe"

[Setup]
AppId={{9C7A42F1-8C0B-4E8D-9B37-1D5F6E12A9C4}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\BookShelf
DefaultGroupName={#AppName}
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=BookShelf.ico
UninstallDisplayIcon={app}\BookShelf.exe
LicenseFile=LICENSE.txt
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
OutputBaseFilename=BookShelf-{#AppVersion}-setup
OutputDir=Output

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Files]
Source: "BookShelf.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\BookShelf.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\BookShelf.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\BookShelf.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
