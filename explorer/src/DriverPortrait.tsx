import { useState } from 'react';

export default function DriverPortrait({ src, code, name }: { src: string; code: string; name: string }) {
  const [failedSource, setFailedSource] = useState<string>();
  return failedSource === src ? (
    <div className="portrait portrait-fallback" role="img" aria-label={`Portrait unavailable for ${name}`} title={`Portrait unavailable for ${name}`}>
      {code}
    </div>
  ) : (
    <img key={src} className="portrait" src={src} alt="" onError={() => setFailedSource(src)} />
  );
}
