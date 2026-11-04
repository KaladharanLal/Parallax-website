import { useEffect, useState } from 'react';
import { ShieldAlert, Video, Eye, Radio, Terminal } from 'lucide-react';

export function PoiHudTopBar({ edition }) {
  const [time, setTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTime(
        d.toISOString().slice(0, 19).replace('T', ' ') + ' UTC'
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="poi-hud-topbar" aria-label="System telemetry">
      <div className="poi-hud-left">
        <span className="poi-rec-indicator">
          <span className="poi-rec-dot" /> REC
        </span>
        <span className="poi-hud-tag">
          <Video size={12} style={{ display: 'inline', marginRight: 4 }} />
          CAM-FEED: NSSCE // PALAKKAD
        </span>
        <span className="poi-hud-tag poi-hud-threat">
          <ShieldAlert size={12} style={{ display: 'inline', marginRight: 4 }} />
          THREAT: ELEVATED
        </span>
      </div>

      <div className="poi-hud-center">
        <span className="poi-hud-tag" style={{ color: '#fff', fontWeight: 700 }}>
          <Eye size={12} style={{ display: 'inline', marginRight: 4, color: '#ff0033' }} />
          SYSTEM: SAMARITAN v4.8
        </span>
      </div>

      <div className="poi-hud-right">
        <span className="poi-hud-tag">
          <Radio size={12} style={{ display: 'inline', marginRight: 4, color: '#38bdf8' }} />
          {edition?.name || 'PARALLAX'} NODE: ONLINE
        </span>
        <span className="poi-hud-tag" style={{ fontVariantNumeric: 'tabular-nums' }}>
          {time}
        </span>
      </div>
    </div>
  );
}

export function PoiSamaritanBanner({ onAction }) {
  const PHRASES = [
    'YOU ARE BEING WATCHED',
    'THE SYSTEM HAS DETECTED THREATS',
    'TWO DAYS OF ENGINEERING ARGUED IN PUBLIC',
    'CALCULATING OPTIMAL RESPONSE...',
    'WHAT ARE YOUR COMMANDS ?',
    'SEE BEYOND THE OBVIOUS',
    'PARALLAX // ACCESS LEVEL 1 GRANTED',
  ];

  const [phraseIndex, setPhraseIndex] = useState(0);
  const [wordIndex, setWordIndex] = useState(0);
  const [currentWord, setCurrentWord] = useState('');

  useEffect(() => {
    const words = PHRASES[phraseIndex].split(' ');
    let timer;

    if (wordIndex < words.length) {
      setCurrentWord(words[wordIndex]);
      timer = setTimeout(() => {
        setWordIndex((w) => w + 1);
      }, 550);
    } else {
      timer = setTimeout(() => {
        setWordIndex(0);
        setPhraseIndex((p) => (p + 1) % PHRASES.length);
      }, 2000);
    }

    return () => clearTimeout(timer);
  }, [phraseIndex, wordIndex]);

  return (
    <div
      className="poi-banner-samaritan"
      onClick={onAction}
      title="Samaritan Artificial Intelligence Interface"
    >
      <div className="poi-banner-text">{currentWord || '...'}</div>
      <div className="poi-banner-icon" />
      <div className="poi-banner-sub">
        /// PRIMARY INTELLIGENCE DIRECTIVE // ALL CHANNELS ACTIVE
      </div>
    </div>
  );
}

