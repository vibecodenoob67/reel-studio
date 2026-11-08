import {useEffect, useReducer} from 'react';

// Every public/<name>/render.json (written by tools/prep.py). Kept on globalThis so a preview that is already open
// reads the new version after prep runs (the component keeps its old module scope across a fast refresh).
export type Word = {w: string; s: number; e: number};
export type Piece = {file: string; from: number; frames: number; audio?: boolean; zoom: number};
export type Moment = {kind: 'zoom' | 'text' | 'emoji'; from: number; frames: number; text?: string; emoji?: string; x?: number; y?: number; amount?: number};
export type Style = {font: string; color: string; highlight: string; stroke: string; size: number; y: number; uppercase: boolean};
export type Render = {
  id: string; fps: number; width: number; height: number; frames: number;
  voice: string | null; music: {file: string; volume: number} | null;
  clips: Piece[]; broll: Piece[]; words: Word[]; captions: boolean; progress: boolean;
  hook: {text: string; frames: number} | null; moments: Moment[]; style: Style;
};

declare const require: {context: (dir: string, deep: boolean, re: RegExp) => {keys: () => string[]; (k: string): Render}};
const ctx = require.context('../public', true, /render\.json$/);
const g = globalThis as unknown as {reelVideos: Record<string, Render>};
g.reelVideos = Object.fromEntries(ctx.keys().map((k) => [ctx(k).id, ctx(k)]));
export const videos = () => g.reelVideos;

// redraw an open, paused preview when prep writes a new render.json
if (typeof window !== 'undefined') window.dispatchEvent(new Event('reel-update'));
export const useVideos = () => {
  const [, bump] = useReducer((x: number) => x + 1, 0);
  useEffect(() => {
    window.addEventListener('reel-update', bump);
    return () => window.removeEventListener('reel-update', bump);
  }, []);
  return g.reelVideos;
};
