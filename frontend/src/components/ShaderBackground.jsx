import './ShaderBackground.css';

/**
 * Darwin Wisp - Iframe Implementation
 * Loads Darwin's wisp animation via iframe like the original
 */
export default function ShaderBackground() {
  return (
    <div className="wisp-background">
      <iframe 
        src="/wisp/index.html" 
        title="Wisp Animation"
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
          display: 'block',
          margin: 0,
          padding: 0
        }}
      />
      {/* Subtle dim overlay */}
      <div className="wisp-dim-overlay" />
    </div>
  );
}
