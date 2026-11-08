import {Composition} from 'remotion';
import {videos} from './data';
import {Edit} from './Edit';

// every video with a public/<name>/render.json (written by tools/prep.py) shows up in the preview sidebar
export const Root = () => (
  <>
    {Object.values(videos()).map((r) => (
      <Composition key={r.id} id={r.id} component={Edit} durationInFrames={r.frames} fps={r.fps}
        width={r.width} height={r.height} defaultProps={{id: r.id}} />
    ))}
  </>
);
