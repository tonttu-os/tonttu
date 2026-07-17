# Project Spec: "Tonttu"
### A retro-gaming appliance OS that is also a real Linux machine

**Status:** Draft v0.6 · **Official name:** Tonttu OS (always shortened to "Tonttu") · **Target:** x86_64 mini-PCs and HTPCs · **License posture:** FOSS (custom components Apache-2.0; upstreams keep their licenses), no bundled ROMs/BIOS

---

## 1. Concept

A Linux distribution that boots directly into an EmulationStation-style couch UI (like Batocera), but underneath is a normal, maintainable, general-purpose Linux system. Users get the appliance experience by default — power on, pick a game, play — while retaining the ability to run desktop apps (Firefox, VLC), self-hosted services (Jellyfin, llama.cpp server), and containers (Docker/Podman) without fighting the OS.

**One-sentence pitch:** *Batocera's UX on Bazzite's architecture.*

### Why Batocera itself can't do this
Batocera is built with Buildroot: a fully cross-compiled, read-only squashfs image with no package manager. Every emulator, library, and app is compiled into the image by the Batocera team. That's why you can't `apt install firefox` on it — there's no mechanism for it. Adding general-purpose capability to Batocera means rebuilding Batocera's entire build system, which is the single most expensive part of that project (they maintain toolchains for ~40 SBC targets).

### The core insight
Every requirement in this project already exists as a mature component. The only genuinely new work is **integration and polish**:

| Requirement | Already solved by |
|---|---|
| Couch frontend | ES-DE (MIT-licensed on Linux, actively developed) |
| Emulator backend | RetroArch + Flathub standalone emulators (Dolphin, xemu, PCSX2, DuckStation, melonDS, PPSSPP…) |
| Immutable, appliance-grade base OS | Fedora Atomic / bootc OCI images (the Bazzite model) |
| Desktop apps | Flatpak (Firefox, VLC from Flathub) |
| Services | Podman quadlets / Docker Compose (Jellyfin, llama.cpp containers) |
| Image build + CI | Containerfile + GitHub Actions (Universal Blue image-template) |
| Install path | Phase 1: `bootc switch` onto existing Fedora Atomic installs (helper script). Phase 2: self-contained installer at maturity. |

The project is therefore **highly feasible for a small team or even one person**, *provided* the scope stays disciplined (see §3).

---

## 2. Prior art and positioning

| Project | Base | Appliance UX | General-purpose | Notes |
|---|---|---|---|---|
| Batocera | Buildroot | ★★★ | ✗ | The UX benchmark. Closed to extension. |
| Lakka | LibreELEC | ★★★ | ✗ | RetroArch-only, even more locked down. |
| RetroPie | Raspbian/Debian overlay | ★★ | ✓ | Right philosophy, aging tech, Pi-centric, mutable base rots over time. |
| ChimeraOS | Arch, A/B images | ★★★ | ~ | Steam-first, retro is secondary. |
| Bazzite (+HTPC mode) | Fedora Atomic (bootc) | ★★ | ★★★ | The architecture benchmark. Steam Big Picture frontend, not ES. |
| RetroDECK | Flatpak (app, not OS) | ★★ | n/a | ES-DE + emulators in one Flatpak; proof the emulator bundle works. |

**The gap this project fills:** nothing today combines a retro-first ES-DE boot-to-frontend experience with an immutable-but-extensible general-purpose base. Bazzite is closest architecturally; Batocera is closest experientially. This project is the intersection.

---

## 3. Key simplifications (the important section)

These decisions convert a multi-year distro project into a months-scale integration project:

1. **Do not build a distro from scratch. Build an OS *image*.**
   Base on **vanilla Fedora Atomic via bootc**: the OS is defined by a single `Containerfile` layered on Fedora's `base` bootc image. GitHub Actions builds and publishes the image; installed machines update atomically from the registry. You inherit Fedora's security updates, kernel, Mesa, and driver work forever, at zero cost. Starting from the plain base (rather than a gaming derivative like Bazzite) means nothing to strip out — no Steam, no desktop environment, no upstream product decisions to fight — at the cost of owning a few small additions ourselves: gamescope, controller udev rules, and multimedia codecs (all available as packages; ublue's repos serve as reference for the udev/codec bits without taking their whole image).

2. **Do not fork EmulationStation.** Use upstream ES-DE. It's MIT-licensed on Linux, supports standalone emulators natively via `es_systems.xml` find-rules, has themes, scraping, and controller config built in. Custom behavior goes in config files and a small companion settings app, not a fork. (Batocera maintains a heavy ES fork with OS settings baked in — that's a permanent maintenance tax to avoid.)

3. **Do not package emulators.** RetroArch and every needed standalone emulator (Dolphin, xemu, PCSX2, DuckStation, PPSSPP, melonDS, Flycast, MAME…) are maintained on Flathub by their own teams. ES-DE already ships find-rules for Flatpak emulator IDs. The OS image pre-installs a curated Flatpak set on first boot; updates come from Flathub, decoupled from OS releases. This also sidesteps the legal churn around console emulators — if one is taken down or forked (as happened with Yuzu/Ryujinx), you update a manifest list, not your build system.

4. **Do not package desktop apps either.** Firefox, VLC, Kodi = Flatpaks. The base image stays tiny and boring.

5. **Services are containers, not packages.** Jellyfin, llama.cpp server, *arr apps, etc. run as Podman quadlets (systemd-native containers) toggled from a services menu. Docker CE can be layered for users who want it. Nothing service-related touches the OS image except the container runtime and a small toggle UI.

6. **x86_64 only for v1.** Batocera burns most of its effort on ~40 ARM SBC targets with per-board kernels and GPU blobs. Skip all of it. Target generic UEFI x86_64 (mini PCs, NUCs, old laptops, handhelds like ROG Ally later via Bazzite's existing handheld support). ARM (Pi 5) can be a v3 exploration once bootc ARM support matures.

7. **One display architecture, one mode:** Wayland kiosk, always. A **cage** session runs ES-DE fullscreen; there is **no desktop mode**. Desktop apps are not a separate world — they appear *inside* ES-DE as an "Apps" system and launch fullscreen exactly like games (§5.7). **Gamescope is not the session** — it's a per-title tool: any game system or app can be toggled to launch inside a nested gamescope (for upscaling, resolution caps, HDR) via its catalog YAML field and a settings-menu toggle. This kills an entire class of complexity: no second session, no display manager, no session hand-off scripts, no Plasma/GNOME in the image (hundreds of MB smaller), one consistent input model (gamepad + phone remote) everywhere, and no dependence on gamescope's GPU-specific quirks for basic operation. Power users get SSH and distrobox; a terminal can even be an "app."

8. **Ship nothing legally risky.** No ROMs, no console BIOS files, no keys (xemu needs an Xbox BIOS; PS2/Dreamcast need BIOS; Switch emulation needs keys). First-boot wizard tells users where to place their own files (`/userdata/bios`, validated with an MD5 checker like Batocera's). This is both the legal and the ethical line, and it's the industry-standard one.

### What deliberately stays out of scope (v1 non-goals)
Netplay infrastructure, cloud save sync, ARM boards, NVIDIA legacy GPUs, CRT/15kHz output, Android app support, a custom theme engine, a web-based settings UI, and any bundled copyrighted content.

---

## 4. Refined concept

> **Tonttu is a bootc-based Fedora Atomic image that boots into ES-DE as a Wayland kiosk. Games run through RetroArch and Flathub standalone emulators. Desktop apps (Firefox, VLC, Kodi…) appear inside ES-DE as an "Apps" console — each app browses like a ROM and launches fullscreen like a game. A "Services" menu enables self-hosted containers (Jellyfin, llama.cpp, Docker workloads) as systemd quadlets. All user content lives on a separate `/userdata` area that survives OS updates and reinstalls. OS updates are atomic image swaps with automatic rollback. There is no desktop mode — the couch UI is the only UI.**

Three user personas, one system:
- **Player:** never leaves the couch UI. Appliance semantics: it always boots, updates can't brick it (rollback), a factory reset never touches saves/ROMs.
- **Tinkerer:** installs extra Flatpaks (they auto-appear in the Apps system), uses the phone remote for keyboard/mouse-driven apps, and drops to SSH/distrobox for a mutable Arch/Debian userland when real terminal work is needed.
- **Homelabber:** toggles Jellyfin (pointed at the same media/ROM disk), runs a llama.cpp server on the box's GPU while it idles, makes the always-on box the household's Home Assistant hub, deploys arbitrary containers.

---

## 5. Architecture

### 5.1 Layer stack

```
┌──────────────────────────────────────────────────────┐
│  User content (/var/userdata): roms, bios, saves,    │
│  media, containers volumes, flatpak user data        │  ← never touched by updates
├──────────────────────────────────────────────────────┤
│  Flatpaks: RetroArch, Dolphin, xemu, PCSX2, Firefox, │
│  VLC …  (Flathub, auto-updating, user-extensible)    │
├──────────────────────────────────────────────────────┤
│  Services: Podman quadlets (jellyfin, llama-cpp, …)  │
├──────────────────────────────────────────────────────┤
│  Tonttu image layer (Containerfile):               │
│   ES-DE, gamescope session, tonttu-settings,         │
│   tonttu-web, apps-sync, first-boot wizard,          │
│   catalogs, controller udev rules, codecs, branding  │
├──────────────────────────────────────────────────────┤
│  Base image: vanilla Fedora Atomic (bootc base)      │
│   kernel, Mesa, PipeWire, NetworkManager, Podman,    │
│   Flatpak, bootc                                     │
└──────────────────────────────────────────────────────┘
```

### 5.2 Boot and session flow

1. systemd-boot/GRUB → bootc-managed root (A/B: rollback to previous image on failure).
2. `greetd` (or plain systemd unit) auto-logs the `tonttu` user into a **cage** Wayland session running ES-DE fullscreen. No desktop, no panels; boot-to-frontend in seconds after first setup.
3. ES-DE presents:
   - **Game systems** (SNES, PS2, …) — the normal ES-DE experience.
   - **Apps system** — Firefox, VLC, Kodi and any user-installed Flatpak, browsed like ROMs and launched fullscreen (§5.7). **Settings** (`tonttu-settings`) is a default, mandatory entry in this row — Wi-Fi, Bluetooth pairing, audio out, updates, catalog/service toggles, factory reset — gamepad-navigable and launched fullscreen like everything else. It cannot be hidden or removed. This is the largest piece of net-new code in the project.
4. Emulator launches: ES-DE `es_find_rules.xml` resolves each system to `flatpak run org.libretro.RetroArch -L <core>` or the standalone Flatpak ID. Per-system overrides editable by the user.
5. **First-boot install mechanics:** Flatpaks cannot ship inside a bootc image (they live in `/var`), so the mandatory set (RetroArch) and catalog defaults install on first boot, *after* the wizard's network step — network connection is therefore the wizard's first order of business (Phase-1 hosts already have it). **Show-activity is a universal rule during initial install:** every download/install renders visible progress, never a blank screen or silently empty system list. Once the system is running, shell/progress dialogs are hidden by default and exposable as a user preference.

### 5.3 Storage layout

| Path | Contents | Update-safe | Notes |
|---|---|---|---|
| `/usr` (image) | OS + ES-DE + session | replaced atomically | read-only |
| `/etc` | machine config | 3-way merged by bootc | |
| `/var/userdata/roms/<system>/` | ROMs | ✓ | ES-DE ROM dir; Samba/SFTP-exported |
| `/var/userdata/bios/` | user-supplied BIOS/keys | ✓ | MD5 validation tool |
| `/var/userdata/saves`, `/states` | saves, savestates | ✓ | symlinked/configured into each emulator's Flatpak data dir |
| `/var/userdata/media/` | movies/music for Jellyfin/Kodi | ✓ | |
| `/var/userdata/containers/` | quadlet volumes | ✓ | |

Network share (Samba, on by default on LAN) exposes `/var/userdata` so users drag-and-drop ROMs from another machine — table-stakes Batocera behavior.

### 5.4 Catalogs: toggle-to-install apps and services

Apps and services share one model: a **small curated catalog**, presented in the first-boot wizard and the settings menu, where toggling an entry on runs its install action (fetching prebuilt from the official upstream source — Flathub or a container registry; nothing is compiled) and toggling off removes it. Catalog entries are declarative manifests shipped in the image, so adding an entry is a data change, not code — and community-contributable.

**App catalog.** Each entry = name, description, icon, and an install script that pulls from the app's official upstream source (Flathub for Firefox, VLC, Kodi, emulators). Toggling on installs; `apps-sync` (§5.7) then makes it appear in the ES-DE Apps row automatically. Nothing is compiled at install time and nothing enters the OS image — the catalog is curation, not packaging.

**Catalog format.** Entries are **fully declarative YAML** — data, never executable code. The catalog manager generates install actions from typed fields (`type: flatpak` → ref + remote; `type: container` → image, volumes, port), and each entry's `settings` block auto-generates its gamepad-navigable form. The official catalog ships read-only in the image (`/usr/share/tonttu/catalog/`); users may drop additional YAML files into `/var/userdata/catalogs/` (hand-written or downloaded community catalogs). Files merge at load, official entries win ID collisions, and everything from userdata is badged **unofficial** with a confirm dialog on install. The format is schema-versioned (`catalog_version`) from day one.

**Custom passthrough fields.** Typed fields exist for options that need a gamepad-editable settings form; everything else uses two freeform passthrough fields, so unmapped flags never require a schema change: **`custom_runtime_args`** (extra podman flags for services; extra gamescope flags for apps) and **`custom_app_args`** (appended to the program's own command line). Strings are shlex-tokenized into argv and passed directly — never evaluated by a shell — so YAML remains data that can only parameterize the one command Tonttu was already going to run. A typed field is added to the schema only when an option needs a UI or a safety wrapper; otherwise it lives in `custom` forever (same philosophy as quadlets' own `PodmanArgs=`).

**Trust model (walled garden with a marked gate).** Official entries are vetted; unofficial entries trade safety for freedom, and the UI makes that trade explicit:
- Installing any entry from an unofficial catalog **requires the admin password**, not just a confirm tap. The admin password is the `tonttu` user's password, set during first boot and checked via **polkit — one password controls all privileged actions** (unofficial installs, SSH enable, factory reset).
- The install dialog displays the entry's custom args verbatim, and the catalog manager pattern-matches high-risk flags (`--privileged`, `--cap-add`, host networking, device/volume mounts outside `/var/userdata`) to escalate the warning: *"This service requests full system access."*
- Unofficial entries carry a persistent **UNVERIFIED badge for as long as they exist** — on the settings service list, as an ES-DE badge on Apps-row entries, and on the `tonttu-web` status page — not just at install time.

**Service catalog.** Each entry = a Podman quadlet template + a manifest declaring the *minimal* settings that service genuinely needs. Because the list is small and curated, we expose only a handful of fields per service rather than a generic config editor:

- **jellyfin** — settings: media folder(s) (default `/var/userdata/media`, ROM folder optional for game-video libraries); GPU transcode on/off (VA-API device passthrough). Port fixed at default.
- **llama-cpp** — the toggle is a guided setup, not just a container start:
  1. **Hardware scan:** detect GPU vendor/VRAM (or CPU-only + system RAM) — same probe that picks the Vulkan/ROCm/CUDA image variant.
  2. **Model recommendation:** map the hardware tier to a **curated model table** shipped as catalog data (e.g. ≤8 GB RAM CPU-only → small 3–4B chat model at Q4; 8–12 GB VRAM → 7–8B Q5; 16–24 GB VRAM → 13–14B or high-quant 8B; 24 GB+ → 30B-class). Table entries are general-use instruct/chat models with permissive licenses, each pinned to a specific Hugging Face GGUF repo/file + recommended context size and offload settings. The table lives in its own **`models.yaml`** catalog file: a baseline ships in the image, and the catalog manager can fetch a signed, updated copy from the official Tonttu catalog endpoint ("Refresh model list" in settings), so recommendations track the model landscape independent of OS releases. Users can also drop their own model-table YAML into `/var/userdata/catalogs/` (badged unofficial, as usual).
  3. **Download:** fetch the GGUF from Hugging Face into `/var/userdata/models/` with resumable download, checksum verification, progress bar in the settings UI (and disk-space preflight check).
  4. **Launch and listen:** start the quadlet with the recommended presets (context window, GPU offload layers, flash-attention where supported) and expose the OpenAI-compatible endpoint on the LAN; endpoint URL + QR shown in settings and on the `tonttu-web` landing page.
  - Manual overrides remain: weights file picker over `/var/userdata/models/*.gguf` (users can drop in their own models via the web uploader or Samba), context size preset, GPU offload on/off. "Recommended" is the default path, not a cage.
- **home-assistant** — official container image; settings: USB device passthrough picker (Zigbee/Z-Wave sticks detected via udev), config folder (default `/var/userdata/containers/homeassistant`). Runs with host networking so device discovery (mDNS/SSDP) works; web UI on its standard port 8123, linked from the settings menu and `tonttu-web` landing page. The always-on HTPC box is a natural smart-home hub.
- **docker** — a single on/off toggle that enables dockerd for users bringing their own Compose stacks; no further settings, it's the escape hatch.

Settings render as gamepad-navigable forms in `tonttu-settings` (file/folder pickers scoped to `/var/userdata`) and write into the quadlet's environment/volume lines. Enable = install unit + start; disable = stop + remove unit; volumes/data always persist in `/var/userdata/containers/`.

Resource policy: services run in a systemd slice with CPU/IO weights below the game session so a background transcode never causes frame drops. Additionally, each service entry carries a **`suspend_on_play`** preset (a standard field in its settings form): when a game or app launches, flagged services are paused (`systemctl stop` or container freeze) and resumed on return to the frontend. Defaults ship per entry — llama-cpp suspends (GPU/RAM-hungry, stateless), Jellyfin and Home Assistant keep running (household infrastructure shouldn't stop because someone's playing Mario) — and users flip any of them per service.

### 5.5 Update model

- **OS:** `bootc upgrade` on a timer (staged, applies on reboot; automatic rollback if boot fails). Release channels: `stable`, `testing` = image tags.
- **Emulators/apps:** Flatpak auto-update timer.
- **Services:** podman auto-update label on quadlets.
- Three independent update streams means an emulator regression never requires an OS release, and vice versa.

### 5.6 Web UI (`tonttu-web`)

A lightweight web service starts at boot and is reachable from any phone/PC on the LAN at **`http://tonttu.local`** (Avahi/mDNS; IP + QR code shown in the ES-DE settings menu and first-boot wizard). Deliberately limited scope for v1 — it is a companion, not an admin panel.

**Feature 1 — ROM & BIOS upload.**
Drag-and-drop (or phone file picker) upload straight into `/var/userdata`:
- System picker (grid of console logos) routes files to the right `roms/<system>/` folder; file-extension hints warn on obvious mismatches (e.g. `.iso` dropped into `snes`).
- Dedicated BIOS tab uploads to `/var/userdata/bios/` and runs the MD5 checker inline — instant "✓ valid PS2 BIOS / ✗ unknown file" feedback, which is friendlier than a post-hoc report.
- Chunked/resumable uploads (large ISO files over Wi-Fi), progress bars, multi-file queue.
- After upload, triggers an ES-DE gamelist reload (ES-DE supports this via its API/UDP command or a soft restart).
- Samba/SFTP remain available for bulk transfers from PCs; the web uploader is the zero-setup path for phones.

**Feature 2 — Remote keyboard & touchpad.**
When a launched app needs keyboard/mouse (Firefox, Kodi search fields, DOS/point-and-click games, desktop mode), the phone becomes the input device:
- The web page offers a touchpad surface (relative pointer + tap/two-finger scroll) and a full keyboard with modifier keys.
- Transport: WebSocket → backend injects events through a **uinput virtual keyboard/mouse device**, so it works identically for ES-DE, games, and any fullscreen app, including inside Flatpak sandboxes — no per-app integration, the compositor just sees a real input device. (Same mechanism proven by projects like Weylus and KDE Connect.)
- Complementary on-TV option: a controller-navigable on-screen keyboard (e.g. `wvkbd`) bindable to a gamepad chord, for quick text entry without pulling out a phone.
- ES-DE can surface a hint toast ("Need typing? Open tonttu.local on your phone") when launching apps tagged as keyboard-requiring.

**Security model:** service binds to LAN interfaces only, never WAN; first connection from a new device requires a 4-digit PIN displayed on the TV (session token stored thereafter); input-injection and upload endpoints both sit behind that pairing; rate-limited; optional toggle to disable the whole service in settings.

**Implementation:** single small daemon (Go or Python/FastAPI + one static SPA page), systemd unit in the image. Upload is boring file handling; input is ~200 lines of evdev/uinput glue. Estimated size: S–M.

### 5.7 Apps as an ES-DE system ("Apps" console)

Desktop applications are first-class citizens of the frontend, not an escape hatch out of it.

**How it appears:** ES-DE gets a custom system named **Apps** in `es_systems.xml`, shown alongside SNES, PS2, etc., with its own theme artwork (an "Applications" console logo). Entering it lists each app like a game — logo, description, screenshots — and selecting one launches it fullscreen. Exiting the app (quit, or a gamepad hold-chord) returns to ES-DE, exactly like quitting an emulator.

**How it works (all standard ES-DE machinery, no fork):**
- The system's "ROM" directory is `/var/userdata/apps/`, containing one launcher file per app (e.g. `Firefox.app` — a one-line script or a `.desktop`-derived stub).
- The system's launch command runs the target directly under the cage session by default (`flatpak run org.mozilla.firefox`); cage fullscreens it. If the entry's **gamescope toggle** is on, the command is prefixed with a nested gamescope (`gamescope --fullscreen -W … -w … --` ) for forced resolution/scaling, frame caps, or HDR, and to seal apps that spawn stray dialogs.
- **Gamescope toggle:** a per-entry boolean (+ optional flags) in the catalog YAML (`gamescope: {enabled: false, flags: […]}`) for apps, and a per-system setting for game systems, both surfaced as a simple toggle in the settings UI — same pattern as service settings. Users decide per title; initial defaults ship from beta-testing findings.
- **Auto-population:** a small `apps-sync` service (systemd path/timer unit) watches installed Flatpaks, generates/removes launcher stubs, writes `gamelist.xml` metadata, and pulls each app's icon and AppStream screenshots as ES-DE media — so `flatpak install org.videolan.VLC` (via settings, webUI, or SSH) makes VLC simply appear in the Apps row with proper artwork. Uninstall removes it.
- Curated defaults preinstalled: **Settings (mandatory — pinned, cannot be hidden or uninstalled)**, Firefox, VLC, Kodi, a terminal (foot), and the File Manager. Other entries users hide/reorder via normal ES-DE metadata editing.
- Keyboard/mouse-tagged apps trigger the "open tonttu.local on your phone" hint toast on launch (§5.6).

**Why this beats a desktop mode:** one navigation model, one input model, one session to test; the image drops an entire desktop environment; and the appliance never breaks character — Firefox is just another cartridge.

### 5.8 Distribution: phased install path

Because the OS *is* an OCI image, distribution can start with zero installer work:

**Phase 1 (alpha → beta): `bootc switch` onto existing Fedora Atomic systems.**
- Prerequisite: any bootc-based Fedora Atomic install (a fresh minimal Fedora Atomic install is the recommended starting point).
- Onboarding is a **one-script walkthrough**: install Fedora Atomic → download and run `tonttu-install.sh`. The script sanity-checks the host (bootc present, x86_64, disk space, no known conflicting layers), prints what it's about to do, runs `bootc switch ghcr.io/tonttu-os/tonttu:stable`, prepares `/var/userdata`, and reboots into the frontend. First-boot wizard takes it from there.
- **Userdata drive provisioning (before the switch):** the script offers to dedicate a drive or partition to userdata — pick a disk/partition, format it, create the standard folder structure (`roms/`, `models/`, `media/`, `saves/`…), move any existing files onto it, and install a systemd mount unit for `/var/userdata`. Apps and services need no remapping afterward because everything already resolves paths through `/var/userdata`. Skipping this keeps userdata on the root disk (fine for small libraries).
- **Alpha input prerequisite:** Phase 1 assumes a wired keyboard/mouse is present during setup — it's required for the Fedora Atomic install anyway — so first-boot text entry (Wi-Fi passwords) needs no on-screen keyboard until the phone remote and wvkbd land in M2.
- **Fresh installs recommended; mergers beware.** Converting a lived-in Silverblue/Bazzite system technically works (and is rollback-safe — the previous deployment remains bootable), but inherited `/etc` drift, layered packages, and existing user accounts are explicitly *supported on a best-effort basis only*. The install script detects a non-fresh system and shows this warning before proceeding.
- Benefits: no ISO pipeline to build or test, instant reversibility (`bootc rollback`) makes trying Tonttu zero-risk, and the alpha/beta audience (tinkerers) is exactly the population comfortable with this path.

**Phase 2 (1.0, once features are mature): self-contained installer / flashable disk image.**
The Batocera-style "flash USB, boot, done" path for the Player persona, built on the standard Anaconda/bootc install flow or a pre-built raw image. Deferred, not dropped — it is what makes Tonttu a true appliance product, but it earns its build/test cost only after the feature set stabilizes.

### 5.9 Backup (`tonttu-backup`)

Saves are the most irreplaceable bytes on the box, so backup is built in and on by default once a target is configured.

- **Targets:** a designated external drive (identified by filesystem UUID) or an SMB/network path, chosen in settings.
- **Folder toggles:** backup scope is per-folder with sensible defaults — saves, states, gamelists, BIOS, configs, and container/service data **on**; large, replaceable content (`roms/`, `media/`, `models/`) **off** by default, each individually toggleable.
- **Backup on detect:** when the designated external device is plugged in, backup starts automatically (udev-triggered) with an on-screen toast and progress, followed by a safe-to-remove notification. Complemented by a scheduled timer when the target is a network path or permanently attached drive.
- **Mechanism:** incremental snapshots (rsync hard-link rotation) — boring, inspectable, restorable file-by-file without special tooling. Restore flow lives in settings; backups survive factory reset by definition (they're off-box).

### 5.10 Power & HDMI-CEC

**Display sleep:** the display blanks (DPMS off) after a user-set idle duration (no gamepad/keyboard/mouse/remote input). Video playback inhibits it — the compositor honors the Wayland idle-inhibit protocol, which Kodi, VLC, and Firefox already request during playback.

**System sleep:** the box suspends after a second user-set duration *following* display sleep. Each service catalog entry carries an **`inhibit_system_sleep`** preset (same pattern as `suspend_on_play`): while any enabled service has it set, system sleep is blocked — display sleep is unaffected. Shipping defaults: Home Assistant **on** (a smart-home hub must not nap), Jellyfin **on** (mid-episode on the TV in the other room), Docker **on** (unknown workloads, fail safe), llama-cpp **off**. Wake sources: power button, controller wake where hardware supports it (USB/BT), CEC, and an optional Wake-on-LAN toggle for homelabbers.

**HDMI-CEC:** enabled via libcec — TV remote navigates ES-DE and Kodi, powering on the box switches the TV to the right input, and the TV remote can wake the box. Honest hardware caveat: most x86 GPUs do not expose CEC pins, so on typical mini-PCs this requires a Pulse-Eight USB-CEC adapter (or a motherboard/handheld that wires it). Tonttu detects CEC hardware and shows the settings only when present; without it, everything else works normally.

### 5.11 Sustainability: annual porridge

Per folklore, a tonttu is paid once a year in a bowl of porridge. This is the project's entire monetization model — a voluntary annual donation ritual, never a paywall.

- **Trigger:** winter solstice ("porridge season"), computed from a solstice-date table bundled in the image (pure data, no network needed); if unavailable, default to **December 22**. One shared season for all households, like the tradition it borrows from.
- **Prompt:** a single low-pressure surface in settings and on the `tonttu-web` landing page — *"It's porridge season."* Links (URL + QR) to an external donation platform (GitHub Sponsors / OpenCollective). **No payment code ships in the box.**
- **Recording a donation, offline:** after donating, the platform's thank-you email contains a **4-digit PIN**. The box computes the same PIN locally — it is derived per-year from a project key baked into the image (truncated HMAC over the year) — so entering it works with no webhooks, no accounts, no calling home, fully offline. This is ceremonial-grade verification by design: the key is extractable and the PIN is guessable, which is fine, because there is nothing behind the door to steal. It exists to make feeding the tonttu a deliberate little ritual, not to enforce payment.
- **"Years fed" counter:** stored in `/var/userdata` (inside default backup scope), shown as a fireside tally ("3 winters of porridge").
- **Unfed tonttu:** no nags, no locks, no feature gates — **ever**. The only consequence is sad, unobtrusive graphics (an empty-bowl icon in a corner of the settings menu). A "never ask again" toggle exists and carries no penalty beyond that permanent, subtle empty bowl.

### 5.12 Trust invariant: the tonttu tends, never watches

Personifying "a little guy who lives in your machine" must stay warm, never eerie — a hard product rule, not a copy suggestion:

- **Copy invariant:** no UI text may imply observation, listening, or awareness ("Tonttu noticed…", "while you were away Tonttu saw…"). He acts only when invited (a toggle, a schedule, a plugged-in backup drive) and *takes nothing home*.
- **Radical network transparency:** the product proves the claim. A small, always-available indicator shows when outgoing traffic is happening, and a readable log of external connections (which service/app, which destination, when) is one click away in settings and on `tonttu-web`. Telemetry remains zero; the log is expected to show nothing but the user's own Flatpak updates, image pulls, and enabled services.

---

## 6. Component choices (v1)

| Concern | Choice | Rationale / fallback |
|---|---|---|
| Base image | Vanilla Fedora Atomic bootc base | Nothing to strip (no Steam, no DE); we add gamescope, controller udev rules, codecs ourselves (ublue repos as reference, not as base). |
| Build system | Containerfile + GitHub Actions (ublue image-template) | Free CI, signed images, zero infra; every build boot-tested in a VM (smoke test: reaches ES-DE). |
| Frontend | ES-DE 3.x, **packaged by us as a CI-built RPM** pinned to upstream release tags (approved exception to the no-compile guardrail — upstream ships AppImage only) | MIT on Linux, standalone-emulator native, themable, scraper built in. ES-DE + RetroArch + Settings are the three mandatory installs by design. Fallback: Pegasus. |
| Kiosk compositor | cage session, always on; gamescope as per-title nested toggle (YAML field + settings UI, defaults set from beta testing) | Cage = boring and GPU-agnostic; gamescope used only where scaling/HDR earns its keep. |
| Login | greetd autologin | |
| Apps system | ES-DE custom system + `apps-sync` generator (Flatpak → launcher stubs + gamelist + icons) | No desktop environment in the image. |
| Retro cores | RetroArch Flatpak + libretro cores | |
| Standalones | Dolphin, xemu, PCSX2, DuckStation, PPSSPP, melonDS, Flycast, MAME (Flathub) | Switch/3DS emulators: user-installable, not preloaded (legal prudence). |
| Apps | Curated catalog toggles (Firefox, VLC, Kodi, terminal, file manager) installing from official upstream sources; user-extensible via any Flatpak | |
| Container runtime | Podman + quadlets (Docker as catalog toggle) | Podman is preinstalled on Fedora Atomic and rootless-friendly. |
| Catalogs | Declarative, schema-versioned YAML manifests (no executable code); official set in image + unofficial user catalogs in `/var/userdata/catalogs/` | Community-contributable data, not code; unofficial entries badged + confirm dialog. |
| Settings app | New: `tonttu-settings`, a dedicated gamepad-navigable app (Qt/Kirigami or SDL), shipped as a mandatory pinned entry in the Apps console | Biggest custom component; a script-menu stopgap is acceptable during alpha only. |
| File sharing | Web uploader (primary, phone-friendly) + Samba/SFTP (bulk) | |
| Web UI | New: `tonttu-web` daemon (Go or FastAPI) + static SPA; uinput for remote input | Avahi mDNS for `tonttu.local`; PIN pairing. |
| On-screen keyboard | wvkbd (gamepad-invoked) | Complement to phone remote. |
| First-boot | Wizard: language, Wi-Fi, controller, **admin password creation**, userdata location, ROM/BIOS instructions | The wizard *is* tonttu-settings in first-run mode — one codebase. Admin password gates privileged actions (unofficial installs, SSH enable, factory reset). |
| Backups | New: `tonttu-backup` — folder toggles, backup-on-detect (udev), rsync snapshots | Off-box by design; restore flow in settings. |
| Power/CEC | systemd + Wayland idle-inhibit; libcec (Pulse-Eight on typical x86) | Per-service `inhibit_system_sleep` presets; CEC settings shown only when hardware present. |
| Remote access | SSH **off by default**; enabling it in settings forces setting a password or key first | No default credentials, ever (the Batocera `root/linux` lesson). |

---

## 7. Custom software to actually write

Honest inventory of net-new code (everything else is configuration):

1. **tonttu-settings** (M) — gamepad-navigable settings UI: network, BT pairing, audio/display, update channel, service toggles, factory reset. ~The whole differentiated UX lives here.
2. **First-boot wizard** (S) — tonttu-settings in first-run mode; not a separate codebase.
3. **apps-sync** (S) — Flatpak watcher that generates Apps-system launcher stubs, gamelist.xml metadata, and icon/screenshot media from AppStream data.
4. **Catalog manager** (S–M) — shared backend for app + service toggles: schema-versioned YAML manifest format, install/remove actions generated from typed fields (no embedded scripts), quadlet templating with minimal per-service settings (paths, weights file, USB passthrough, on/off flags), custom-args passthrough (shlex→argv, no shell), high-risk-flag scanner, admin-password gate for unofficial installs, persistent UNVERIFIED badge plumbing (settings, ES-DE badges, tonttu-web), unofficial-catalog loading, status reporting.
5. **Model recommender + fetcher** (S) — hardware probe (VRAM/RAM/GPU vendor) → lookup in curated model table → resumable Hugging Face GGUF download with checksum + disk-space preflight → write llama.cpp quadlet presets. Table maintenance is ongoing curation work, not code.
6. **BIOS checker** (XS) — MD5 manifest validator with friendly output in ES-DE.
7. **ES-DE integration glue** (S) — es_systems/find_rules overlay for Flatpak IDs, custom menu entries, default theme/branding.
8. **Save-path unification** (S) — per-emulator config so saves land in `/var/userdata` (RetroDECK has prior art to study).
9. **tonttu-web** (S–M) — LAN web companion: ROM/BIOS uploader with system routing + inline MD5 validation, and remote keyboard/touchpad via WebSocket→uinput. PIN pairing, mDNS discovery.
10. **tonttu-install.sh** (S) — Phase-1 onboarding script: host sanity checks, fresh-vs-merged detection + warning, optional userdata drive provisioning (disk picker, format, folder structure, data migration, mount unit), `bootc switch`, reboot.
11. **tonttu-session** (S) — session orchestrator: launch wrapper around games/apps that enforces the global force-quit gamepad chord (evdev-level, works regardless of what's focused), triggers `suspend_on_play` stops/resumes, manages idle-inhibit and sleep timers, fires hint toasts, and keeps gamepad input from reaching a backgrounded ES-DE.
12. **tonttu-backup** (S) — backup engine: target config (UUID/SMB), per-folder scope, udev backup-on-detect with toast/progress, rsync hard-link snapshots, restore flow.
13. **ES-DE packaging** (S) — CI-built RPM from upstream source, pinned to release tags; the approved exception to the no-compile rule. Ongoing: bump-and-rebuild per upstream release.
14. **Boot/shutdown splash** (XS) — Plymouth theme from marketing's static portal/mascot images (door opens on boot, closes on shutdown). Nothing fancy: static images, no animation engine. Request art files from marketing when built.
15. **Network transparency log** (S) — per-service/app outgoing-connection logging (nftables/conntrack), the outgoing-traffic indicator, and the connection-log views in settings + tonttu-web (§5.12).
16. **Porridge module** (XS) — solstice-table date check, prompt surfaces, HMAC PIN check, years-fed counter, empty-bowl state (§5.11). Part of tonttu-settings + tonttu-web, listed separately for scope honesty.

Rough total: one experienced developer can reach a credible alpha in ~2–4 months of focused work; the long tail is device/controller/edge-case polish, which is community-shaped work anyway.

---

## 8. Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **Emulator legal climate** (Nintendo takedowns) | Med | Don't bundle Switch/3DS emulators or any keys/BIOS; Flatpak model means removals are manifest edits. Ship nothing Nintendo-current. |
| **ES-DE upstream direction** (Android port is partially closed; desktop remains MIT) | Low-Med | Desktop Linux build is MIT and forkable at last resort; keep customizations config-side so migration to Pegasus is possible. |
| **Flatpak friction** (portals, controller/udev access, save paths inside sandboxes) | Med | RetroDECK proves it's solvable; ship per-app Flatpak overrides in the image; document escape hatch (layered RPM emulators). |
| **NVIDIA** | Med | Bazzite base has NVIDIA image variants; support AMD/Intel first-class, NVIDIA best-effort. |
| **App window behavior under cage** (multi-window apps, splash screens, focus quirks) | Med | Curate the default app list to well-behaved apps; per-entry gamescope toggle seals misbehaving titles; phone remote covers pointer needs. |
| **Scope creep into "distro brain"** (custom package builds, ARM boards, kernel patches) | High | This spec's simplification rules are the guardrail. Any proposal that adds a compile step to the OS build needs extraordinary justification. |
| **Services vs. gaming resource contention** | Low | systemd slices + per-service `suspend_on_play` presets. |
| **Web UI attack surface** (input injection = remote control of the box) | Med | LAN-only bind, mandatory PIN pairing per device, token expiry, kill-switch in settings, no WAN/UPnP exposure ever. |
| **Converted ("merged") systems in Phase 1** (inherited /etc drift, layered packages, unexpected user setups) | Med | Recommend fresh Fedora Atomic installs; install script detects non-fresh hosts and warns; best-effort support only; rollback always available. |
| **Unofficial catalog entries** (arbitrary images/refs + custom flags = user-authorized risk) | Med | Admin password required to install; verbatim display of custom args; high-risk-flag warning escalation; persistent UNVERIFIED badge while installed; shlex-to-argv only, never shell. |
| **CEC hardware variability on x86** (most GPUs lack CEC pins) | Low | libcec + Pulse-Eight USB adapters as the supported path; feature auto-hides without hardware; never a core dependency. |
| **Owning hardware enablement** (controller udev rules, codecs, HDR — no longer inherited from a gaming base) | Med | These exist as discrete packages/rule files; vendor a minimal set into the image layer and crib from ublue/Bazzite repos as reference. Scope stays small because v1 targets generic x86_64, not handheld quirks. |

---

## 9. Milestones

**M0 — Proof of architecture (1–2 weeks)**
Fork ublue image-template pointed at the vanilla Fedora Atomic bootc base; layer cage + controller udev rules + ES-DE autologin; preinstall RetroArch + Dolphin + Firefox Flatpaks; manually verify boot-to-frontend → launch game → quit → frontend, launch Firefox fullscreen from a hand-made Apps entry → quit → frontend, **and** the same entry with the nested-gamescope prefix toggled on. Also verify input isolation: gamepad input must not reach the backgrounded ES-DE while a game runs. All M0 verification is done bare-metal on the **reference box: HP EliteDesk 800 G1 DM** (Haswell iGPU = the honest performance floor), plus the CI VM smoke test.

**M1 — Alpha (4–8 weeks)** *(PM note: before starting save-path work (#8), mine RetroDECK's public configs — save paths and per-emulator Flatpak overrides are solved problems there.)*
Userdata layout + Samba; ES-DE find-rules for full Flatpak emulator set; save-path unification; first-boot wizard v0 **with app catalog toggles**; **Apps system with apps-sync auto-population**; **Phase-1 distribution: published OCI image + `tonttu-install.sh` switch script + fresh-vs-merge warning**; branding + default theme; **tonttu-web v0: ROM/BIOS uploader with mDNS + PIN pairing**; CI boot smoke test on every image build. SSH ships off by default from day one.

**M2 — Beta**
tonttu-settings app (network/BT/audio/updates); **per-title gamescope toggles in settings UI (collect beta data to set shipping defaults)**; **service catalog with Jellyfin + llama.cpp (hardware-scan model recommendation + HF download) + Home Assistant + Docker toggles and minimal per-service settings forms**; BIOS checker (integrated into web uploader); update channels + rollback UX; handheld target validation (ROG Ally class); **tonttu-web v1: remote keyboard/touchpad + on-screen keyboard chord**; **tonttu-backup with folder toggles + backup-on-detect**; **power policy (display/system sleep, per-service inhibit presets) + CEC support**.

**M3 — 1.0**
**Phase-2 distribution: self-contained installer / flashable disk image (Anaconda-bootc or raw image)**; docs, factory-reset, community service catalog, hardware compatibility list, theme polish, telemetry-free crash reporting opt-in.

---

## 10. Open questions

1. ~~Bazzite vs. vanilla base~~ **Decided: vanilla Fedora Atomic.** Follow-up: which specific hardware-enablement bits to vendor in (controller udev rules, HDR bits, handheld quirks) and whether to track ublue's packages for them or maintain our own minimal set.
2. ~~Session compositor~~ **Decided: cage always on; gamescope as a per-title toggle in catalog YAML + settings UI.** Follow-up: which entries default the toggle on — to be determined from beta-testing data.
3. ~~Catalog curation policy~~ **Decided: no formal curation pipeline for now.** Community additions live in unofficial YAML catalog files (`/var/userdata/catalogs/`), badged as such. As the platform grows, adopt Discord (or similar) for community submissions, voting, and promotion of entries into the official catalog.
4. ~~Settings app placement/technology~~ **Decided: a dedicated app, shipped as a default, mandatory entry in the Apps console** (pinned alongside Firefox etc., launched fullscreen like everything else). Script-menu shortcuts may bridge the alpha, but the app is the product.
5. ~~Project name~~ **Decided: Tonttu** (official: "Tonttu OS", always shortened to Tonttu; see naming memo — lore, mascot rules, and porridge model all approved). **Proceeding at risk** ahead of formal counsel + Finland PRH check; handles use the `tonttu-os` suffix (registry `ghcr.io/tonttu-os/tonttu`, hostname `tonttu.local`).
6. Process: from M0 the spec lives as `SPEC.md` at the repo root, with this decision history preserved alongside it.
