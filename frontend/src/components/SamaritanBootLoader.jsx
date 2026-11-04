import { useEffect, useRef, useState } from 'react';

const LOGO = `${import.meta.env.BASE_URL}images/Parallax Brochure Design Assets/Parallax Design Utilities/logos/logo.png`;

const PARALLAX_LOGS = [
  'x0.0/sirv',
  '+0.1/ecom',
  '[eth0] LINK_ESTABLISHED',
  '[eth1] 1000BASE-T GIGABIT',
  'node_1 [NSSCE_PALAKKAD]',
  'node_2 [CONVENTION_CORE]',
  'node_3 [AUDITORIUM_STAGE]',
  'node_4 [LAB_COMPLEX]',
  'node_5 [INNOVATION_HUB]',
  'feed_1 [PALAKKAD_CAMPUS]',
  'feed_2 [LIVE_TELEMETRY]',
  'feed_3 [REGISTRATION_DESK]',
  'subsys [PASS_ALLOCATOR]',
  'subsys [BIOMETRIC_AUTH]',
  'subsys [ALL_SYSTEMS_GO]',
];

const PARALLAX_RESOURCES = [
  'parallax.core.kernel',
  'parallax.network.nssce_node',
  'parallax.identity.pass_matrix',
  'parallax.events.hackathon_24h',
  'parallax.events.coding_sprint',
  'parallax.events.paper_presentation',
  'parallax.events.project_expo',
  'parallax.events.circuit_debugging',
  'parallax.workshops.cad_robotics',
  'parallax.security.biometrics',
  'parallax.sigint.telemetry_active',
  'samaritan.parallax.online',
];

export function SamaritanBootLoader({ onComplete }) {
  const [phase, setPhase] = useState('opening');
  const [progress, setProgress] = useState(0);
  const [currentResource, setCurrentResource] = useState(PARALLAX_RESOURCES[0]);
  const [logs, setLogs] = useState([]);
  const [blinkCursor, setBlinkCursor] = useState(true);
  const [paneWidth, setPaneWidth] = useState('50%');
  const rafRef = useRef(null);

  // Blinking cursor effect for LOADING _
  useEffect(() => {
    const curInterval = setInterval(() => {
      setBlinkCursor((b) => !b);
    }, 320);
    return () => clearInterval(curInterval);
  }, []);

  // Immediate smooth aperture opening on mount (zero start lag)
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setPaneWidth('20%');
    });

    const tLoading = setTimeout(() => {
      setPhase('loading');
    }, 120);

    return () => {
      cancelAnimationFrame(frame);
      clearTimeout(tLoading);
    };
  }, []);

  // Streaming logs and 60fps smooth progress fill
  useEffect(() => {
    if (phase !== 'loading') return undefined;

    let logIdx = 0;
    const logInterval = setInterval(() => {
      if (logIdx < PARALLAX_LOGS.length) {
        setLogs((prev) => [...prev, PARALLAX_LOGS[logIdx]]);
        logIdx++;
      } else {
        clearInterval(logInterval);
      }
    }, 65);

    const startTime = performance.now();
    const duration = 1100;

    const updateFrame = (now) => {
      const elapsed = now - startTime;
      const pct = Math.min(100, Math.round((elapsed / duration) * 100));
      setProgress(pct);

      const resIdx = Math.min(
        PARALLAX_RESOURCES.length - 1,
        Math.floor((pct / 100) * PARALLAX_RESOURCES.length)
      );
      setCurrentResource(PARALLAX_RESOURCES[resIdx]);

      if (pct < 100) {
        rafRef.current = requestAnimationFrame(updateFrame);
      } else {
        clearInterval(logInterval);

        setPhase('connected');

        setTimeout(() => {
          // Switch to command screen with Parallax LOGO
          setPhase('command');

          setTimeout(() => {
            // Unveil: panes glide to 0%
            setPhase('unveiling');
            setPaneWidth('0%');

            setTimeout(() => {
              setPhase('done');
              if (onComplete) onComplete();
            }, 450);
          }, 950);
        }, 500);
      }
    };

    rafRef.current = requestAnimationFrame(updateFrame);

    return () => {
      clearInterval(logInterval);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [phase, onComplete]);

  if (phase === 'done') return null;

  return (
    <div className={`samaritan-boot-screen ${phase === 'unveiling' ? 'fade-out' : ''}`}>
      {/* Left Pane (Aperture shutter) */}
      <div
        className="samaritan-pane samaritan-pane-left"
        style={{ width: paneWidth }}
      >
        <div className="samaritan-overlay-cap left-cap" />
        <div className="samaritan-boot-log">
          {logs.map((line, idx) => (
            <div key={idx} className="samaritan-log-line">
              <span className="samaritan-bracket">[</span>
              <span className="samaritan-log-num">{idx < 10 ? ` 0${idx}` : idx}</span>
              <span className="samaritan-bracket">]</span>
              <span className="samaritan-log-text">{line}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Center Main Display Pane */}
      <div className="samaritan-pane-center">
        {/* Phase: Opening or Loading */}
        {(phase === 'opening' || phase === 'loading') && (
          <div className="samaritan-loader-box">
            {/* Parallax Convention Logo */}
            <div className="samaritan-brand-lockup">
              <img src={LOGO} alt="PARALLAX" className="samaritan-brand-logo" />
              <div className="samaritan-brand-sub">
                ISTE STUDENT CHAPTER · NSS COLLEGE OF ENGINEERING, PALAKKAD
              </div>
            </div>

            {/* Inverted Loading Badge */}
            <div className="samaritan-badge-row">
              <span className="samaritan-invert-badge">
                LOADING <span className="samaritan-cursor">{blinkCursor ? '_' : ' '}</span>
              </span>
            </div>

            {/* Cycling Resource Stream */}
            <div className="samaritan-resource-name">{currentResource}</div>

            {/* Clean Progress Bar Container */}
            <div className="samaritan-bar-wrap">
              <div
                className="samaritan-bar-fill"
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="samaritan-pct-label">{progress}%</div>
          </div>
        )}

        {/* Phase: Connected */}
        {phase === 'connected' && (
          <div className="samaritan-connected-box">
            <span className="samaritan-invert-badge large">
              CONNECTION ESTABLISHED
            </span>
          </div>
        )}

        {/* Phase: Command Screen (PARALLAX LOGO instead of plain text) */}
        {phase === 'command' && (
          <div className="samaritan-command-box">
            <div className="samaritan-message-container">
              <img src={LOGO} alt="PARALLAX" className="samaritan-command-logo" />
              <hr className="samaritan-command-hr" />
            </div>

            <div className="samaritan-marker">
              <span className="samaritan-triangle">&#9650;</span>
            </div>

            <div className="samaritan-command-sub">
              WHAT ARE YOUR COMMANDS ?
            </div>

            <div className="samaritan-command-kicker">
              SYSTEM ONLINE // ACCESS LEVEL 1 GRANTED
            </div>
          </div>
        )}
      </div>

      {/* Right Pane (Aperture shutter) */}
      <div
        className="samaritan-pane samaritan-pane-right"
        style={{ width: paneWidth }}
      >
        <div className="samaritan-overlay-cap right-cap" />
        <div className="samaritan-right-decor">
          <div className="samaritan-sys-tag">ISTE NSSCE NODE</div>
          <div className="samaritan-sys-sub">PARALLAX v4.8</div>
        </div>
      </div>
    </div>
  );
}
