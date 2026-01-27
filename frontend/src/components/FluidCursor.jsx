import { useEffect, useRef } from 'react';

export default function FluidCursor() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function pointerPrototype() {
      this.id = -1;
      this.texcoordX = 0;
      this.texcoordY = 0;
      this.prevTexcoordX = 0;
      this.prevTexcoordY = 0;
      this.deltaX = 0;
      this.deltaY = 0;
      this.down = false;
      this.moved = false;
      this.color = [0, 0, 0];
    }

    let config = {
      SIM_RESOLUTION: 128,
      DYE_RESOLUTION: 512,
      DENSITY_DISSIPATION: 6.5,       // Fades much faster
      VELOCITY_DISSIPATION: 4.5,      // Fades much faster
      PRESSURE: 0.1,
      PRESSURE_ITERATIONS: 20,
      CURL: 2,                        // Less swirly
      SPLAT_RADIUS: 0.05,             // Much smaller splats
      SPLAT_FORCE: 1200,              // Much less force
      SHADING: true,
      COLOR_UPDATE_SPEED: 10,
      PAUSED: false,
      BACK_COLOR: { r: 0, g: 0, b: 0 },
      TRANSPARENT: true,
      MIN_MOVEMENT_THRESHOLD: 0.0005  // Minimum movement to trigger splat
    };

    let pointers = [new pointerPrototype()];

    const { gl, ext } = getWebGLContext(canvas);
    if (!gl) return;

    if (!ext.supportLinearFiltering) {
      config.DYE_RESOLUTION = 256;
      config.SHADING = false;
    }

    function getWebGLContext(canvas) {
      const params = {
        alpha: true,
        depth: false,
        stencil: false,
        antialias: false,
        preserveDrawingBuffer: false
      };
      let gl = canvas.getContext('webgl2', params);
      const isWebGL2 = !!gl;
      if (!isWebGL2) gl = canvas.getContext('webgl', params) || canvas.getContext('experimental-webgl', params);
      if (!gl) return { gl: null, ext: {} };

      let halfFloat;
      let supportLinearFiltering;
      if (isWebGL2) {
        gl.getExtension('EXT_color_buffer_float');
        supportLinearFiltering = gl.getExtension('OES_texture_float_linear');
      } else {
        halfFloat = gl.getExtension('OES_texture_half_float');
        supportLinearFiltering = gl.getExtension('OES_texture_half_float_linear');
      }
      gl.clearColor(0.0, 0.0, 0.0, 1.0);

      const halfFloatTexType = isWebGL2 ? gl.HALF_FLOAT : halfFloat && halfFloat.HALF_FLOAT_OES;
      let formatRGBA, formatRG, formatR;

      if (isWebGL2) {
        formatRGBA = getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, halfFloatTexType);
        formatRG = getSupportedFormat(gl, gl.RG16F, gl.RG, halfFloatTexType);
        formatR = getSupportedFormat(gl, gl.R16F, gl.RED, halfFloatTexType);
      } else {
        formatRGBA = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType);
        formatRG = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType);
        formatR = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType);
      }

      return {
        gl,
        ext: { formatRGBA, formatRG, formatR, halfFloatTexType, supportLinearFiltering }
      };
    }

    function getSupportedFormat(gl, internalFormat, format, type) {
      if (!supportRenderTextureFormat(gl, internalFormat, format, type)) {
        switch (internalFormat) {
          case gl.R16F: return getSupportedFormat(gl, gl.RG16F, gl.RG, type);
          case gl.RG16F: return getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, type);
          default: return null;
        }
      }
      return { internalFormat, format };
    }

    function supportRenderTextureFormat(gl, internalFormat, format, type) {
      const texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, 4, 4, 0, format, type, null);
      const fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
      return gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
    }

    class Program {
      constructor(vertexShader, fragmentShader) {
        this.uniforms = {};
        this.program = createProgram(vertexShader, fragmentShader);
        this.uniforms = getUniforms(this.program);
      }
      bind() { gl.useProgram(this.program); }
    }

    function createProgram(vertexShader, fragmentShader) {
      let program = gl.createProgram();
      gl.attachShader(program, vertexShader);
      gl.attachShader(program, fragmentShader);
      gl.linkProgram(program);
      return program;
    }

    function getUniforms(program) {
      let uniforms = [];
      let uniformCount = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
      for (let i = 0; i < uniformCount; i++) {
        let uniformName = gl.getActiveUniform(program, i).name;
        uniforms[uniformName] = gl.getUniformLocation(program, uniformName);
      }
      return uniforms;
    }

    function compileShader(type, source) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      return shader;
    }

    const baseVertexShader = compileShader(gl.VERTEX_SHADER, `
      precision highp float;
      attribute vec2 aPosition;
      varying vec2 vUv;
      varying vec2 vL, vR, vT, vB;
      uniform vec2 texelSize;
      void main () {
        vUv = aPosition * 0.5 + 0.5;
        vL = vUv - vec2(texelSize.x, 0.0);
        vR = vUv + vec2(texelSize.x, 0.0);
        vT = vUv + vec2(0.0, texelSize.y);
        vB = vUv - vec2(0.0, texelSize.y);
        gl_Position = vec4(aPosition, 0.0, 1.0);
      }
    `);

    const copyShader = compileShader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying highp vec2 vUv;
      uniform sampler2D uTexture;
      void main () { gl_FragColor = texture2D(uTexture, vUv); }
    `);

    const clearShader = compileShader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying highp vec2 vUv;
      uniform sampler2D uTexture;
      uniform float value;
      void main () { gl_FragColor = value * texture2D(uTexture, vUv); }
    `);

    const displayShader = compileShader(gl.FRAGMENT_SHADER, `
      precision highp float;
      varying vec2 vUv;
      uniform sampler2D uTexture;
      void main () {
        vec3 c = texture2D(uTexture, vUv).rgb;
        float a = max(c.r, max(c.g, c.b));
        gl_FragColor = vec4(c, a);
      }
    `);

    const splatShader = compileShader(gl.FRAGMENT_SHADER, `
      precision highp float;
      varying vec2 vUv;
      uniform sampler2D uTarget;
      uniform float aspectRatio;
      uniform vec3 color;
      uniform vec2 point;
      uniform float radius;
      void main () {
        vec2 p = vUv - point.xy;
        p.x *= aspectRatio;
        vec3 splat = exp(-dot(p, p) / radius) * color;
        vec3 base = texture2D(uTarget, vUv).xyz;
        gl_FragColor = vec4(base + splat, 1.0);
      }
    `);

    const advectionShader = compileShader(gl.FRAGMENT_SHADER, `
      precision highp float;
      varying vec2 vUv;
      uniform sampler2D uVelocity;
      uniform sampler2D uSource;
      uniform vec2 texelSize;
      uniform float dt;
      uniform float dissipation;
      void main () {
        vec2 coord = vUv - dt * texture2D(uVelocity, vUv).xy * texelSize;
        vec4 result = texture2D(uSource, coord);
        float decay = 1.0 + dissipation * dt;
        gl_FragColor = result / decay;
      }
    `);

    const divergenceShader = compileShader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying highp vec2 vUv, vL, vR, vT, vB;
      uniform sampler2D uVelocity;
      void main () {
        float L = texture2D(uVelocity, vL).x;
        float R = texture2D(uVelocity, vR).x;
        float T = texture2D(uVelocity, vT).y;
        float B = texture2D(uVelocity, vB).y;
        vec2 C = texture2D(uVelocity, vUv).xy;
        if (vL.x < 0.0) L = -C.x;
        if (vR.x > 1.0) R = -C.x;
        if (vT.y > 1.0) T = -C.y;
        if (vB.y < 0.0) B = -C.y;
        float div = 0.5 * (R - L + T - B);
        gl_FragColor = vec4(div, 0.0, 0.0, 1.0);
      }
    `);

    const curlShader = compileShader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying highp vec2 vUv, vL, vR, vT, vB;
      uniform sampler2D uVelocity;
      void main () {
        float L = texture2D(uVelocity, vL).y;
        float R = texture2D(uVelocity, vR).y;
        float T = texture2D(uVelocity, vT).x;
        float B = texture2D(uVelocity, vB).x;
        float vorticity = R - L - T + B;
        gl_FragColor = vec4(0.5 * vorticity, 0.0, 0.0, 1.0);
      }
    `);

    const vorticityShader = compileShader(gl.FRAGMENT_SHADER, `
      precision highp float;
      varying vec2 vUv, vL, vR, vT, vB;
      uniform sampler2D uVelocity;
      uniform sampler2D uCurl;
      uniform float curl;
      uniform float dt;
      void main () {
        float L = texture2D(uCurl, vL).x;
        float R = texture2D(uCurl, vR).x;
        float T = texture2D(uCurl, vT).x;
        float B = texture2D(uCurl, vB).x;
        float C = texture2D(uCurl, vUv).x;
        vec2 force = 0.5 * vec2(abs(T) - abs(B), abs(R) - abs(L));
        force /= length(force) + 0.0001;
        force *= curl * C;
        force.y *= -1.0;
        vec2 velocity = texture2D(uVelocity, vUv).xy;
        velocity += force * dt;
        velocity = min(max(velocity, -1000.0), 1000.0);
        gl_FragColor = vec4(velocity, 0.0, 1.0);
      }
    `);

    const pressureShader = compileShader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying highp vec2 vUv, vL, vR, vT, vB;
      uniform sampler2D uPressure;
      uniform sampler2D uDivergence;
      void main () {
        float L = texture2D(uPressure, vL).x;
        float R = texture2D(uPressure, vR).x;
        float T = texture2D(uPressure, vT).x;
        float B = texture2D(uPressure, vB).x;
        float divergence = texture2D(uDivergence, vUv).x;
        float pressure = (L + R + B + T - divergence) * 0.25;
        gl_FragColor = vec4(pressure, 0.0, 0.0, 1.0);
      }
    `);

    const gradientSubtractShader = compileShader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying highp vec2 vUv, vL, vR, vT, vB;
      uniform sampler2D uPressure;
      uniform sampler2D uVelocity;
      void main () {
        float L = texture2D(uPressure, vL).x;
        float R = texture2D(uPressure, vR).x;
        float T = texture2D(uPressure, vT).x;
        float B = texture2D(uPressure, vB).x;
        vec2 velocity = texture2D(uVelocity, vUv).xy;
        velocity.xy -= vec2(R - L, T - B);
        gl_FragColor = vec4(velocity, 0.0, 1.0);
      }
    `);

    const blit = (() => {
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, -1, 1, 1, 1, 1, -1]), gl.STATIC_DRAW);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array([0, 1, 2, 0, 2, 3]), gl.STATIC_DRAW);
      gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(0);
      return (target, clear = false) => {
        if (target == null) {
          gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
          gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        } else {
          gl.viewport(0, 0, target.width, target.height);
          gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo);
        }
        if (clear) {
          gl.clearColor(0.0, 0.0, 0.0, 1.0);
          gl.clear(gl.COLOR_BUFFER_BIT);
        }
        gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);
      };
    })();

    let dye, velocity, divergence, curl, pressure;

    const copyProgram = new Program(baseVertexShader, copyShader);
    const clearProgram = new Program(baseVertexShader, clearShader);
    const splatProgram = new Program(baseVertexShader, splatShader);
    const advectionProgram = new Program(baseVertexShader, advectionShader);
    const divergenceProgram = new Program(baseVertexShader, divergenceShader);
    const curlProgram = new Program(baseVertexShader, curlShader);
    const vorticityProgram = new Program(baseVertexShader, vorticityShader);
    const pressureProgram = new Program(baseVertexShader, pressureShader);
    const gradientSubtractProgram = new Program(baseVertexShader, gradientSubtractShader);
    const displayProgram = new Program(baseVertexShader, displayShader);

    function createFBO(w, h, internalFormat, format, type, param) {
      gl.activeTexture(gl.TEXTURE0);
      let texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, param);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, param);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, w, h, 0, format, type, null);
      let fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
      gl.viewport(0, 0, w, h);
      gl.clear(gl.COLOR_BUFFER_BIT);
      return {
        texture, fbo, width: w, height: h,
        texelSizeX: 1.0 / w, texelSizeY: 1.0 / h,
        attach(id) {
          gl.activeTexture(gl.TEXTURE0 + id);
          gl.bindTexture(gl.TEXTURE_2D, texture);
          return id;
        }
      };
    }

    function createDoubleFBO(w, h, internalFormat, format, type, param) {
      let fbo1 = createFBO(w, h, internalFormat, format, type, param);
      let fbo2 = createFBO(w, h, internalFormat, format, type, param);
      return {
        width: w, height: h, texelSizeX: fbo1.texelSizeX, texelSizeY: fbo1.texelSizeY,
        get read() { return fbo1; },
        set read(v) { fbo1 = v; },
        get write() { return fbo2; },
        set write(v) { fbo2 = v; },
        swap() { let t = fbo1; fbo1 = fbo2; fbo2 = t; }
      };
    }

    function getResolution(resolution) {
      let aspectRatio = gl.drawingBufferWidth / gl.drawingBufferHeight;
      if (aspectRatio < 1) aspectRatio = 1.0 / aspectRatio;
      const min = Math.round(resolution);
      const max = Math.round(resolution * aspectRatio);
      if (gl.drawingBufferWidth > gl.drawingBufferHeight) return { width: max, height: min };
      else return { width: min, height: max };
    }

    function initFramebuffers() {
      let simRes = getResolution(config.SIM_RESOLUTION);
      let dyeRes = getResolution(config.DYE_RESOLUTION);
      const texType = ext.halfFloatTexType;
      const rgba = ext.formatRGBA;
      const rg = ext.formatRG;
      const r = ext.formatR;
      const filtering = ext.supportLinearFiltering ? gl.LINEAR : gl.NEAREST;
      gl.disable(gl.BLEND);

      if (!dye) dye = createDoubleFBO(dyeRes.width, dyeRes.height, rgba.internalFormat, rgba.format, texType, filtering);
      if (!velocity) velocity = createDoubleFBO(simRes.width, simRes.height, rg.internalFormat, rg.format, texType, filtering);
      divergence = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
      curl = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
      pressure = createDoubleFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
    }

    initFramebuffers();
    let lastUpdateTime = Date.now();
    let animationId;

    function updateFrame() {
      const dt = calcDeltaTime();
      resizeCanvas();
      applyInputs();
      step(dt);
      render();
      animationId = requestAnimationFrame(updateFrame);
    }

    function calcDeltaTime() {
      let now = Date.now();
      let dt = (now - lastUpdateTime) / 1000;
      dt = Math.min(dt, 0.016666);
      lastUpdateTime = now;
      return dt;
    }

    function resizeCanvas() {
      let width = Math.floor(canvas.clientWidth * (window.devicePixelRatio || 1));
      let height = Math.floor(canvas.clientHeight * (window.devicePixelRatio || 1));
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
    }

    function applyInputs() {
      pointers.forEach(p => {
        if (p.moved) {
          p.moved = false;
          splatPointer(p);
        }
      });
    }

    function step(dt) {
      gl.disable(gl.BLEND);

      curlProgram.bind();
      gl.uniform2f(curlProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(curlProgram.uniforms.uVelocity, velocity.read.attach(0));
      blit(curl);

      vorticityProgram.bind();
      gl.uniform2f(vorticityProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(vorticityProgram.uniforms.uVelocity, velocity.read.attach(0));
      gl.uniform1i(vorticityProgram.uniforms.uCurl, curl.attach(1));
      gl.uniform1f(vorticityProgram.uniforms.curl, config.CURL);
      gl.uniform1f(vorticityProgram.uniforms.dt, dt);
      blit(velocity.write);
      velocity.swap();

      divergenceProgram.bind();
      gl.uniform2f(divergenceProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(divergenceProgram.uniforms.uVelocity, velocity.read.attach(0));
      blit(divergence);

      clearProgram.bind();
      gl.uniform1i(clearProgram.uniforms.uTexture, pressure.read.attach(0));
      gl.uniform1f(clearProgram.uniforms.value, config.PRESSURE);
      blit(pressure.write);
      pressure.swap();

      pressureProgram.bind();
      gl.uniform2f(pressureProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(pressureProgram.uniforms.uDivergence, divergence.attach(0));
      for (let i = 0; i < config.PRESSURE_ITERATIONS; i++) {
        gl.uniform1i(pressureProgram.uniforms.uPressure, pressure.read.attach(1));
        blit(pressure.write);
        pressure.swap();
      }

      gradientSubtractProgram.bind();
      gl.uniform2f(gradientSubtractProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      gl.uniform1i(gradientSubtractProgram.uniforms.uPressure, pressure.read.attach(0));
      gl.uniform1i(gradientSubtractProgram.uniforms.uVelocity, velocity.read.attach(1));
      blit(velocity.write);
      velocity.swap();

      advectionProgram.bind();
      gl.uniform2f(advectionProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
      let velocityId = velocity.read.attach(0);
      gl.uniform1i(advectionProgram.uniforms.uVelocity, velocityId);
      gl.uniform1i(advectionProgram.uniforms.uSource, velocityId);
      gl.uniform1f(advectionProgram.uniforms.dt, dt);
      gl.uniform1f(advectionProgram.uniforms.dissipation, config.VELOCITY_DISSIPATION);
      blit(velocity.write);
      velocity.swap();

      gl.uniform1i(advectionProgram.uniforms.uVelocity, velocity.read.attach(0));
      gl.uniform1i(advectionProgram.uniforms.uSource, dye.read.attach(1));
      gl.uniform1f(advectionProgram.uniforms.dissipation, config.DENSITY_DISSIPATION);
      blit(dye.write);
      dye.swap();
    }

    function render() {
      gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.enable(gl.BLEND);
      displayProgram.bind();
      gl.uniform1i(displayProgram.uniforms.uTexture, dye.read.attach(0));
      blit(null);
    }

    function splatPointer(pointer) {
      let dx = pointer.deltaX * config.SPLAT_FORCE;
      let dy = pointer.deltaY * config.SPLAT_FORCE;
      splat(pointer.texcoordX, pointer.texcoordY, dx, dy, pointer.color);
    }

    function splat(x, y, dx, dy, color) {
      splatProgram.bind();
      gl.uniform1i(splatProgram.uniforms.uTarget, velocity.read.attach(0));
      gl.uniform1f(splatProgram.uniforms.aspectRatio, canvas.width / canvas.height);
      gl.uniform2f(splatProgram.uniforms.point, x, y);
      gl.uniform3f(splatProgram.uniforms.color, dx, dy, 0.0);
      gl.uniform1f(splatProgram.uniforms.radius, config.SPLAT_RADIUS / 100.0);
      blit(velocity.write);
      velocity.swap();

      gl.uniform1i(splatProgram.uniforms.uTarget, dye.read.attach(0));
      gl.uniform3f(splatProgram.uniforms.color, color.r, color.g, color.b);
      blit(dye.write);
      dye.swap();
    }

    function updatePointerMoveData(pointer, posX, posY) {
      pointer.prevTexcoordX = pointer.texcoordX;
      pointer.prevTexcoordY = pointer.texcoordY;
      pointer.texcoordX = posX / canvas.width;
      pointer.texcoordY = 1.0 - posY / canvas.height;
      let aspectRatio = canvas.width / canvas.height;
      pointer.deltaX = (pointer.texcoordX - pointer.prevTexcoordX) * (aspectRatio < 1 ? aspectRatio : 1);
      pointer.deltaY = (pointer.texcoordY - pointer.prevTexcoordY) / (aspectRatio > 1 ? aspectRatio : 1);
      // Only trigger splat if movement exceeds threshold (prevents blob on small movements)
      const movementMagnitude = Math.sqrt(pointer.deltaX * pointer.deltaX + pointer.deltaY * pointer.deltaY);
      pointer.moved = movementMagnitude > config.MIN_MOVEMENT_THRESHOLD;
    }

    // Subtle purple color palette
    function generateColor() {
      const colors = [
        { r: 0.25, g: 0.12, b: 0.4 },   // Subtle purple
        { r: 0.2, g: 0.1, b: 0.35 },    // Deep purple
        { r: 0.3, g: 0.15, b: 0.45 },   // Light purple
        { r: 0.18, g: 0.08, b: 0.3 },   // Dark purple
      ];
      return colors[Math.floor(Math.random() * colors.length)];
    }

    const handleMouseMove = (e) => {
      let pointer = pointers[0];
      let posX = (e.clientX) * (window.devicePixelRatio || 1);
      let posY = (e.clientY) * (window.devicePixelRatio || 1);
      pointer.color = generateColor();
      updatePointerMoveData(pointer, posX, posY);
    };

    window.addEventListener('mousemove', handleMouseMove);
    animationId = requestAnimationFrame(updateFrame);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 2,
        pointerEvents: 'none'
      }}
    />
  );
}
