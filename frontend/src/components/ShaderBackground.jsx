import { useEffect, useRef } from 'react';
import './ShaderBackground.css';

export default function ShaderBackground() {
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) {
      console.error('WebGL not supported');
      return;
    }

    // Set clear color to black
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    const vertexShaderSource = `
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    // Fixed shader - proper color accumulation
    const fragmentShaderSource = `
      precision highp float;
      uniform float u_time;
      uniform vec2 u_resolution;
      
      vec3 palette(float d) {
        return mix(vec3(0.2, 0.7, 0.9), vec3(1.0, 0.0, 1.0), d);
      }
      
      vec2 rotate(vec2 p, float a) {
        float c = cos(a);
        float s = sin(a);
        return p * mat2(c, s, -s, c);
      }
      
      float map(vec3 p) {
        for(int i = 0; i < 8; ++i) {
          float t = u_time * 0.2;
          p.xz = rotate(p.xz, t);
          p.xy = rotate(p.xy, t * 1.89);
          p.xz = abs(p.xz);
          p.xz -= 0.5;
        }
        return dot(sign(p), p) / 5.0;
      }
      
      vec4 rm(vec3 ro, vec3 rd) {
        float t = 0.0;
        vec3 col = vec3(0.0);
        float d = 0.0;
        
        for(float i = 0.0; i < 64.0; i++) {
          vec3 p = ro + rd * t;
          d = map(p) * 0.5;
          
          if(d < 0.02) {
            break;
          }
          if(d > 100.0) {
            break;
          }
          
          // Accumulate color with proper distance falloff
          float distFactor = 400.0 * d;
          if(distFactor > 0.0) {
            vec3 pal = palette(length(p) * 0.1);
            col += pal / distFactor;
          }
          
          t += d;
        }
        
        // Return color with proper alpha
        float alpha = 1.0;
        if(d > 0.0 && d < 100.0) {
          alpha = 1.0 / (d * 100.0);
        }
        return vec4(col, alpha);
      }
      
      void main() {
        vec2 fragCoord = gl_FragCoord.xy;
        vec2 uv = (fragCoord - (u_resolution.xy / 2.0)) / u_resolution.x;
        
        vec3 ro = vec3(0.0, 0.0, -50.0);
        ro.xz = rotate(ro.xz, u_time);
        
        vec3 cf = normalize(-ro);
        vec3 cs = normalize(cross(cf, vec3(0.0, 1.0, 0.0)));
        vec3 cu = normalize(cross(cf, cs));
        
        vec3 uuv = ro + cf * 3.0 + uv.x * cs + uv.y * cu;
        vec3 rd = normalize(uuv - ro);
        
        vec4 col = rm(ro, rd);
        
        // Ensure we have a proper color output
        gl_FragColor = vec4(col.rgb, 1.0);
      }
    `;

    function createShader(gl, type, source) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compile error:', gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    }

    function createProgram(gl, vertexShader, fragmentShader) {
      const program = gl.createProgram();
      gl.attachShader(program, vertexShader);
      gl.attachShader(program, fragmentShader);
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error('Program link error:', gl.getProgramInfoLog(program));
        gl.deleteProgram(program);
        return null;
      }
      return program;
    }

    const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
    const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);
    const program = createProgram(gl, vertexShader, fragmentShader);

    if (!program) return;

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    const positions = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

    const positionLocation = gl.getAttribLocation(program, 'a_position');
    const timeLocation = gl.getUniformLocation(program, 'u_time');
    const resolutionLocation = gl.getUniformLocation(program, 'u_resolution');

    function resize() {
      const displayWidth = canvas.clientWidth;
      const displayHeight = canvas.clientHeight;
      if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
        canvas.width = displayWidth;
        canvas.height = displayHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
    }

    function render(time) {
      timeRef.current = time * 0.001;
      resize();
      
      // Clear to black each frame
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(program);
      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
      gl.enableVertexAttribArray(positionLocation);
      gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

      gl.uniform1f(timeLocation, timeRef.current);
      gl.uniform2f(resolutionLocation, canvas.width, canvas.height);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animationFrameRef.current = requestAnimationFrame(render);
    }

    animationFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return <canvas ref={canvasRef} className="shader-background" />;
}
