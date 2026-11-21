# Generuje polskie nagranie reklamy (Windows SAPI, glos pl-PL) do fixtures/stt.
param([string]$Out = "fixtures/stt/ad_pl_risk_late.wav")
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$v = $s.GetInstalledVoices() | ? { $_.VoiceInfo.Culture.Name -eq "pl-PL" } | select -First 1
if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$s.SetOutputToWaveFile((Join-Path (Get-Location) $Out), $fmt)
$pb = New-Object System.Speech.Synthesis.PromptBuilder
$pb.StartVoice([System.Globalization.CultureInfo]"pl-PL")
$pb.AppendText("Zarabiaj nawet dwadziescia procent rocznie z naszym funduszem.")
$pb.AppendBreak([TimeSpan]::FromSeconds(4))
$pb.AppendText("Dolacz do tysiecy zadowolonych klientow juz dzisiaj.")
$pb.AppendBreak([TimeSpan]::FromSeconds(3))
$pb.AppendText("Inwestowanie wiaze sie z ryzykiem utraty kapitalu.")
$pb.EndVoice()
$s.Speak($pb)
$s.Dispose()
