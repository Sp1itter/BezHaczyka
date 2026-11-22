# Instalacja Dockera na Windows

Uruchom w PowerShell **jako administrator**:

```
dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
winget install --id Docker.DockerDesktop -e --source winget
```

Potem **restart komputera**, a po restarcie, znowu jako administrator:

```
wsl --update
```

Uruchom Docker Desktop (pierwszy start trwa ok. minuty) i sprawdź:

```
docker version
docker compose version
```

Znane problemy:
- `wsl --install` może zwrócić **403 (Zabroniony)** przy pobieraniu pakietu — dlatego funkcje
  włączamy przez `dism`, a WSL aktualizujemy po restarcie (`wsl --update`) albo instalujemy
  `winget install --id Microsoft.WSL -e`.
- Instalator WSL zwraca `Access is denied`, dopóki nie zrobisz restartu po `dism`.
- Docker Desktop wymaga członkostwa w grupie `docker-users` (instalator dodaje bieżącego
  użytkownika; po instalacji wyloguj się i zaloguj ponownie).
- `ports are not available ... forbidden by its access permissions` — Windows (Hyper-V/WSL)
  rezerwuje zakresy portów i blokuje bind. Sprawdź: `netsh interface ipv4 show excludedportrange protocol=tcp`
  i zmień port w `infra/.env` na spoza zakresów. Dlatego dashboard jest na 7090 (8090 i 3000 bywają zarezerwowane).
- Wirtualizacja musi być włączona w BIOS/UEFI (Menedżer zadań → Wydajność → CPU → „Wirtualizacja: Włączone”).

