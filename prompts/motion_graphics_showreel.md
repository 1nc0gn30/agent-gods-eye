# Agent God's Eye — 15-Second Motion Graphics Showreel Blueprint
**Product**: AGENT GOD'S EYE (`agent-gods-eye`) — Autonomous Shodan OSINT Tactical Radar  
**Hero Anchor Shape**: The *Orbital Lens of Providence* (A rotating dual-concentric gold/cyan targeting reticle with pulsating lat/long coordinate blips and an iris core aperture)  
**Aspect Ratio**: 16:9 (1920x1080) / 9:16 (1080x1920) Vertical Cut  
**Color Palette**: Obsidian Void (`#08080B`), Sovereign Gold (`#D4AF37`), Radar Cyan (`#06B6D4`), Hazard Crimson (`#EF4444`)  
**Target Duration**: 15.0 Seconds (450 Frames @ 30fps)

---

## Storyboard & Timing Breakdown

### [00:00 - 00:03] Scene 1: The Dark Earth Awakens (Frames 0 - 90)
- **Visual**: Camera starts in pitch-black void. A faint whisper of gold aurora mesh gradients (`radial-gradient(circle, #D4AF37 12%, transparent)`) emerges from the center. The *Orbital Lens of Providence* expands from a single bright cyan point with high-tension spring physics (`stiffness: 280, damping: 22`).
- **Kinetic Elements**: Latitude and longitude grid rings snap into concentric focus with a fine dashed phosphor glow.
- **Copy**: 
  - Eyebrow: `GLOBAL ATTACK SURFACE SURVEILLANCE`
  - Headline: `THE PLANET IS LISTENING.`
- **SFX / Procedural Audio**: Low sub-bass riser (40Hz ramp to 90Hz) with high-frequency radar ping chirp (2400Hz).

### [00:03 - 00:07] Scene 2: Target Vector Lock & Threat Matrix (Frames 90 - 210)
- **Visual**: The 3D planetary wireframe rotates smoothly. 1,420 coordinate vectors erupt across Tokyo, Frankfurt, San Jose, and São Paulo. Glowing blips pulse in ruby red and amber.
- **Data UI Overlay**: Bento HUD telemetry panes slide in from the left and right:
  - `SHODAN INTELLIGENCE: CONNECTED`
  - `SCADA / MODBUS / RTSP CAMERAS: 1,842 DETECTED`
  - `THREAT INDEX: 94 / 100 [CRITICAL]`
- **Copy**: `ZERO PIP DEPENDENCIES. 100% PURE PYTHON STANDARD LIBRARY.`
- **SFX / Procedural Audio**: Rapid tactile mechanical clicks (data burst packet stream), followed by warning klaxon chime (-14 LUFS).

### [00:07 - 00:11] Scene 3: Deep Host Dissection & SSE Stream (Frames 210 - 330)
- **Visual**: Camera zooms directly into a red target node at `37.7749° N, 122.4194° W`. The HUD disassembles the host into live banner feeds, open ports (`554 RTSP`, `502 Modbus`, `5900 VNC`), and CVE vulnerabilities badges.
- **Kinetic Transition**: A glowing laser scan line sweeps horizontally across the screen, revealing real-time Server-Sent Events (SSE) telemetry logs running on Port 8112.
- **Copy**: `TACTICAL RECON IN SECONDS. ZERO CLOUD TELEMETRY.`
- **SFX / Procedural Audio**: Deep metallic servo lock sound followed by rapid terminal keystroke ticks.

### [00:11 - 00:15] Scene 4: The Sovereign Treasury Call-to-Action (Frames 330 - 450)
- **Visual**: Camera pulls back into high orbit. The *Orbital Lens of Providence* forms a golden seal around the central title card. Dual payment badges flare with pure CSS conic border beams: Stripe ($19 Lifetime Founding Access) + Solana DePay.
- **Copy**:
  - Main Title: `AGENT GOD'S EYE`
  - Tagline: `Autonomous Shodan OSINT Tactical Radar`
  - Pricing: `FOUNDING LIFETIME: $19 (REGULAR $79)`
  - URL: `godseye.nullai.tech • Engineered by Neal Frazier Tech (@1nc0gn30)`
- **SFX / Procedural Audio**: Orchestral sub-drop, bright crystalline resolve chime, and smooth vinyl taper.

---

## Production Remotion / Revid Automation Recipe

```tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const GodsEyeShowreel: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Orbital Lens Spring Entrance
  const scale = spring({ frame, fps, config: { damping: 20, stiffness: 220 } });
  const rotation = interpolate(frame, [0, 450], [0, 360]);
  const glowOpacity = interpolate(frame, [0, 90, 400, 450], [0, 0.9, 0.9, 0]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#08080B", color: "#F3F4F6", fontFamily: "Space Grotesk, sans-serif" }}>
      {/* Aurora Ambient Core */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: 800,
          height: 800,
          transform: `translate(-50%, -50%) scale(${scale})`,
          background: "radial-gradient(circle, rgba(212,175,55,0.18) 0%, rgba(6,182,212,0.12) 50%, transparent 70%)",
          borderRadius: "50%",
          filter: "blur(60px)",
          opacity: glowOpacity,
        }}
      />
      {/* Tactical Anchor Shape */}
      <svg
        width="500"
        height="500"
        viewBox="0 0 100 100"
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${scale}) rotate(${rotation}deg)`,
        }}
      >
        <circle cx="50" cy="50" r="44" stroke="#D4AF37" strokeWidth="1" strokeDasharray="3 3" fill="none" opacity="0.6" />
        <circle cx="50" cy="50" r="32" stroke="#06B6D4" strokeWidth="1.2" strokeDasharray="2 4" fill="none" />
        <ellipse cx="50" cy="50" rx="44" ry="16" stroke="#38BDF8" strokeWidth="0.8" fill="none" opacity="0.5" />
        <circle cx="50" cy="50" r="14" fill="#0E121B" stroke="#06B6D4" strokeWidth="2" />
        <circle cx="50" cy="50" r="6" fill="#EF4444" />
      </svg>
    </AbsoluteFill>
  );
};
```
