// The one video template. Every video is just data: public/<name>/render.json, written by tools/prep.py.
import React, {useMemo} from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import * as Anton from '@remotion/google-fonts/Anton';
import * as BebasNeue from '@remotion/google-fonts/BebasNeue';
import * as Inter from '@remotion/google-fonts/Inter';
import * as Montserrat from '@remotion/google-fonts/Montserrat';
import * as Poppins from '@remotion/google-fonts/Poppins';

import {Moment, Piece, Style, Word, useVideos} from './data';

const FONTS: Record<string, {mod: {loadFont: Function; fontFamily: string}; weight: string}> = {
  Montserrat: {mod: Montserrat, weight: '800'}, Poppins: {mod: Poppins, weight: '800'}, Inter: {mod: Inter, weight: '800'},
  Anton: {mod: Anton, weight: '400'}, BebasNeue: {mod: BebasNeue, weight: '400'},
};
const loaded = new Set<string>();
const font = (name: string) => {
  const f = FONTS[name.replace(/\s/g, '')] ?? FONTS.Montserrat;
  if (!loaded.has(f.mod.fontFamily)) {
    loaded.add(f.mod.fontFamily);
    f.mod.loadFont('normal', {weights: [f.weight], subsets: ['latin']});
  }
  return {fontFamily: f.mod.fontFamily, fontWeight: Number(f.weight)};
};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
// 0 outside [0, len), eases up to 1 over `ramp` frames, holds, eases back down
const env = (t: number, len: number, ramp = 6) => (t < 0 || t >= len ? 0 : Math.sin((Math.min(1, t / ramp, (len - t) / ramp) * Math.PI) / 2));

// outlined text: the outline is its own layer behind the letters (CSS text-stroke alone eats into thin letters)
const Outlined = ({children, outline, stroke, style}: {children: React.ReactNode; outline: React.ReactNode; stroke: string; style: React.CSSProperties}) => (
  <div style={{display: 'grid', ...style}}>
    {stroke && <div aria-hidden style={{gridArea: '1/1', color: stroke, WebkitTextStroke: `${Math.round(Number(style.fontSize) / 6)}px ${stroke}`}}>{outline}</div>}
    <div style={{gridArea: '1/1'}}>{children}</div>
  </div>
);

const Clip = ({p, muted}: {p: Piece; muted?: boolean}) => {
  const f = useCurrentFrame();
  const push = interpolate(f, [0, p.frames], [1, 1.03]); // slow push-in so no shot ever sits dead still
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile(p.file)} muted={muted || !p.audio} style={{width: '100%', height: '100%', transform: `scale(${p.zoom * push})`}} />
    </AbsoluteFill>
  );
};

// words -> caption chunks of up to 3 words, breaking at punctuation and pauses
const chunk = (words: Word[]) => {
  const out: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    const prev = words[i - 1];
    if (cur.length && (cur.length >= 3 || /[.,!?;:]$/.test(prev.w) || w.s - prev.e > 0.35)) {
      out.push(cur);
      cur = [];
    }
    cur.push(w);
  });
  if (cur.length) out.push(cur);
  return out;
};

const Captions = ({words, st}: {words: Word[]; st: Style}) => {
  const f = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const t = f / fps;
  const chunks = useMemo(() => chunk(words), [words]);
  const i = chunks.findIndex((c, k) => t >= c[0].s && t < Math.min(chunks[k + 1]?.[0].s ?? Infinity, c[c.length - 1].e + 0.5));
  if (i < 0) return null;
  const c = chunks[i];
  const pop = spring({frame: f - Math.round(c[0].s * fps), fps, config: {damping: 12, stiffness: 260, mass: 0.6}});
  const text = (w: Word) => w.w.replace(/[.,;:]+$/, '');
  const line = (colored: boolean) =>
    c.map((w, k) => {
      const on = t >= w.s && (k === c.length - 1 || t < c[k + 1].s);
      return <span key={k} style={colored ? {color: on ? st.highlight : st.color} : undefined}>{text(w)}{k < c.length - 1 ? ' ' : ''}</span>;
    });
  return (
    <div style={{position: 'absolute', top: st.y * height, left: 0, right: 0, display: 'flex', justifyContent: 'center', transform: `translateY(-50%) scale(${0.85 + 0.15 * pop})`}}>
      <Outlined stroke={st.stroke} outline={line(false)} style={{maxWidth: 820, textAlign: 'center', ...font(st.font), fontSize: st.size, lineHeight: 1.1,
        textTransform: st.uppercase ? 'uppercase' : 'none', filter: 'drop-shadow(0 6px 14px rgba(0,0,0,0.4))'}}>
        {line(true)}
      </Outlined>
    </div>
  );
};

// hook text and text moments: a tilted label that pops in and shrinks away
const Pop = ({text, frames, y, st}: {text: string; frames: number; y: number; st: Style}) => {
  const f = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const inn = spring({frame: f, fps, config: {damping: 11, stiffness: 240, mass: 0.6}});
  const out = interpolate(f, [frames - 5, frames], [1, 0], clamp);
  return (
    <div style={{position: 'absolute', top: y * height, left: 0, right: 0, display: 'flex', justifyContent: 'center', opacity: out,
      transform: `translateY(-50%) scale(${inn * (0.6 + 0.4 * out)}) rotate(-2deg)`}}>
      <div style={{maxWidth: 860, background: st.highlight, color: '#111', ...font(st.font), fontSize: st.size * 1.05, lineHeight: 1.1, padding: '18px 34px',
        borderRadius: 22, textAlign: 'center', textTransform: st.uppercase ? 'uppercase' : 'none', boxShadow: '0 12px 40px rgba(0,0,0,0.35)'}}>{text}</div>
    </div>
  );
};

const Emoji = ({m}: {m: Moment}) => {
  const f = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const s = spring({frame: f, fps, config: {damping: 8, stiffness: 200, mass: 0.7}}) * interpolate(f, [m.frames - 6, m.frames], [1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: (m.x ?? 0.72) * width, top: (m.y ?? 0.42) * height, fontSize: 200, lineHeight: 1,
      transform: `translate(-50%, -50%) scale(${s}) rotate(${Math.sin(f / 4) * 6}deg)`, filter: 'drop-shadow(0 10px 20px rgba(0,0,0,0.35))'}}>{m.emoji}</div>
  );
};

const Progress = ({color, frames}: {color: string; frames: number}) => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 12, width: `${(f / Math.max(1, frames - 1)) * 100}%`, background: color}} />;
};

export const Edit = ({id}: {id: string}) => {
  const r = useVideos()[id];
  const f = useCurrentFrame();
  const zoom = 1 + r.moments.filter((m) => m.kind === 'zoom').reduce((z, m) => z + (m.amount ?? 0.12) * env(f - m.from, m.frames), 0);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`}}>
        {r.clips.map((p, i) => <Sequence key={i} from={p.from} durationInFrames={p.frames} layout="none"><Clip p={p} /></Sequence>)}
        {r.broll.map((p, i) => <Sequence key={i} from={p.from} durationInFrames={p.frames} layout="none"><Clip p={p} muted /></Sequence>)}
      </AbsoluteFill>
      {r.voice && <Audio src={staticFile(r.voice)} />}
      {r.music && <Audio src={staticFile(r.music.file)} volume={r.music.volume} loop />}
      {r.progress && <Progress color={r.style.highlight} frames={r.frames} />}
      {r.captions && <Captions words={r.words} st={r.style} />}
      {r.hook && <Sequence durationInFrames={r.hook.frames} layout="none"><Pop text={r.hook.text} frames={r.hook.frames} y={0.2} st={r.style} /></Sequence>}
      {r.moments.map((m, i) => m.kind === 'zoom' ? null : (
        <Sequence key={i} from={m.from} durationInFrames={m.frames} layout="none">
          {m.kind === 'emoji' ? <Emoji m={m} /> : <Pop text={m.text ?? ''} frames={m.frames} y={m.y ?? 0.32} st={r.style} />}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
