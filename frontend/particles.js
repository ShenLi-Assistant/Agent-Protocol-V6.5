'use strict';

(function initParticleNetwork(global) {
  const DEFAULTS = {
    backgroundColor: 'rgba(5, 10, 20, 0)',
    particleColors: ['#FFFFFF', '#7CC7FF', '#50A9FF'],
    minRadius: 0.9,
    maxRadius: 2.2,
    speed: 0.35,
    baseDensity: 0.00008,
    minParticles: 50,
    maxParticles: 220,
    linkDistance: 125,
    linkLineWidth: 1,
    linkAlpha: 0.45,
    repulseRadius: 130,
    repulseForce: 0.15,
    edgePadding: 24,
    dprCap: 2,
    resizeDebounceMs: 120,
    autoStart: true
  };

  function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
  function mergeOptions(base, override) { return Object.assign({}, base, override || {}); }

  class ParticleNetwork {
    constructor(canvas, options) {
      if (!(canvas instanceof HTMLCanvasElement)) throw new Error('ParticleNetwork requires a valid canvas element.');
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d', { alpha: true });
      if (!this.ctx) throw new Error('2D canvas context is unavailable.');
      this.options = mergeOptions(DEFAULTS, options);
      this.particles = [];
      this.mouse = { x: null, y: null, active: false };
      this.animationFrameId = null;
      this.running = false;
      this.width = 0;
      this.height = 0;
      this.dpr = 1;
      this._resizeTimer = null;
      this._boundAnimate = this._animate.bind(this);
      this._boundOnMouseMove = this._onMouseMove.bind(this);
      this._boundOnMouseLeave = this._onMouseLeave.bind(this);
      this._boundOnTouchMove = this._onTouchMove.bind(this);
      this._boundOnTouchEnd = this._onTouchEnd.bind(this);
      this._boundOnResize = this._onResize.bind(this);
      this._boundOnVisibilityChange = this._onVisibilityChange.bind(this);
      this._setupCanvas();
      this._seedParticles();
      this._attachEvents();
      if (this.options.autoStart) this.start();
    }
    start() {
      if (this.running) return;
      this.running = true;
      this.animationFrameId = global.requestAnimationFrame(this._boundAnimate);
    }
    stop() {
      this.running = false;
      if (this.animationFrameId !== null) {
        global.cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
    }
    destroy() {
      this.stop();
      this._detachEvents();
      this.particles.length = 0;
      if (this._resizeTimer) {
        clearTimeout(this._resizeTimer);
        this._resizeTimer = null;
      }
    }
    _setupCanvas() {
      const rect = this.canvas.getBoundingClientRect();
      const cssWidth = Math.max(1, Math.round(rect.width || this.canvas.clientWidth || global.innerWidth || 1));
      const cssHeight = Math.max(1, Math.round(rect.height || this.canvas.clientHeight || global.innerHeight || 1));
      this.dpr = clamp(global.devicePixelRatio || 1, 1, this.options.dprCap);
      this.width = cssWidth;
      this.height = cssHeight;
      this.canvas.width = Math.round(cssWidth * this.dpr);
      this.canvas.height = Math.round(cssHeight * this.dpr);
      this.canvas.style.width = cssWidth + 'px';
      this.canvas.style.height = cssHeight + 'px';
      this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    }
    _targetParticleCount() {
      const area = this.width * this.height;
      const count = Math.round(area * this.options.baseDensity);
      return clamp(count, this.options.minParticles, this.options.maxParticles);
    }
    _seedParticles() {
      const targetCount = this._targetParticleCount();
      this.particles.length = 0;
      for (let i = 0; i < targetCount; i += 1) this.particles.push(this._createParticle());
    }
    _createParticle() {
      const angle = Math.random() * Math.PI * 2;
      const speed = (Math.random() * 0.6 + 0.4) * this.options.speed;
      return {
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        radius: this.options.minRadius + Math.random() * (this.options.maxRadius - this.options.minRadius),
        color: this.options.particleColors[(Math.random() * this.options.particleColors.length) | 0]
      };
    }
    _attachEvents() {
      global.addEventListener('resize', this._boundOnResize, { passive: true });
      this.canvas.addEventListener('mousemove', this._boundOnMouseMove, { passive: true });
      this.canvas.addEventListener('mouseleave', this._boundOnMouseLeave, { passive: true });
      this.canvas.addEventListener('touchmove', this._boundOnTouchMove, { passive: true });
      this.canvas.addEventListener('touchend', this._boundOnTouchEnd, { passive: true });
      document.addEventListener('visibilitychange', this._boundOnVisibilityChange, { passive: true });
    }
    _detachEvents() {
      global.removeEventListener('resize', this._boundOnResize);
      this.canvas.removeEventListener('mousemove', this._boundOnMouseMove);
      this.canvas.removeEventListener('mouseleave', this._boundOnMouseLeave);
      this.canvas.removeEventListener('touchmove', this._boundOnTouchMove);
      this.canvas.removeEventListener('touchend', this._boundOnTouchEnd);
      document.removeEventListener('visibilitychange', this._boundOnVisibilityChange);
    }
    _onVisibilityChange() {
      if (document.hidden) this.stop();
      else if (this.options.autoStart) this.start();
    }
    _onResize() {
      if (this._resizeTimer) clearTimeout(this._resizeTimer);
      this._resizeTimer = setTimeout(() => {
        this._setupCanvas();
        this._seedParticles();
      }, this.options.resizeDebounceMs);
    }
    _updateMousePosition(clientX, clientY) {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = clientX - rect.left;
      this.mouse.y = clientY - rect.top;
      this.mouse.active = true;
    }
    _onMouseMove(event) { this._updateMousePosition(event.clientX, event.clientY); }
    _onMouseLeave() { this.mouse.active = false; this.mouse.x = null; this.mouse.y = null; }
    _onTouchMove(event) { if (event.touches && event.touches.length > 0) this._updateMousePosition(event.touches[0].clientX, event.touches[0].clientY); }
    _onTouchEnd() { this._onMouseLeave(); }
    _updateParticles() {
      const pad = this.options.edgePadding;
      const repulseRadius = this.options.repulseRadius;
      const repulseRadiusSq = repulseRadius * repulseRadius;
      const repulseForce = this.options.repulseForce;
      for (let i = 0; i < this.particles.length; i += 1) {
        const p = this.particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -pad) p.x = this.width + pad;
        if (p.x > this.width + pad) p.x = -pad;
        if (p.y < -pad) p.y = this.height + pad;
        if (p.y > this.height + pad) p.y = -pad;
        if (this.mouse.active && this.mouse.x !== null && this.mouse.y !== null) {
          const dx = p.x - this.mouse.x;
          const dy = p.y - this.mouse.y;
          const distSq = dx * dx + dy * dy;
          if (distSq > 0.0001 && distSq < repulseRadiusSq) {
            const dist = Math.sqrt(distSq);
            const falloff = 1 - dist / repulseRadius;
            const force = repulseForce * falloff;
            p.vx += (dx / dist) * force;
            p.vy += (dy / dist) * force;
          }
        }
        const maxSpeed = this.options.speed * 1.8;
        const v = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
        if (v > maxSpeed) {
          const scale = maxSpeed / v;
          p.vx *= scale;
          p.vy *= scale;
        }
      }
    }
    _draw() {
      const ctx = this.ctx;
      const { width, height } = this;
      const linkDistance = this.options.linkDistance;
      const linkDistanceSq = linkDistance * linkDistance;
      ctx.clearRect(0, 0, width, height);
      if (this.options.backgroundColor) {
        ctx.fillStyle = this.options.backgroundColor;
        ctx.fillRect(0, 0, width, height);
      }
      for (let i = 0; i < this.particles.length; i += 1) {
        const a = this.particles[i];
        for (let j = i + 1; j < this.particles.length; j += 1) {
          const b = this.particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const distSq = dx * dx + dy * dy;
          if (distSq <= linkDistanceSq) {
            const dist = Math.sqrt(distSq);
            const alpha = this.options.linkAlpha * (1 - dist / linkDistance);
            ctx.strokeStyle = 'rgba(125, 195, 255, ' + alpha.toFixed(4) + ')';
            ctx.lineWidth = this.options.linkLineWidth;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
      for (let i = 0; i < this.particles.length; i += 1) {
        const p = this.particles[i];
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    _animate() {
      if (!this.running) return;
      this._updateParticles();
      this._draw();
      this.animationFrameId = global.requestAnimationFrame(this._boundAnimate);
    }
  }
  function createParticleNetwork(canvas, options) { return new ParticleNetwork(canvas, options); }
  global.createParticleNetwork = createParticleNetwork;
  if (!global.__PARTICLE_NETWORK_AUTOINIT__) {
    global.__PARTICLE_NETWORK_AUTOINIT__ = true;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        const canvas = document.getElementById('particle-network');
        if (canvas) canvas.__particleNetworkInstance = createParticleNetwork(canvas);
      }, { once: true });
    } else {
      const canvas = document.getElementById('particle-network');
      if (canvas) canvas.__particleNetworkInstance = createParticleNetwork(canvas);
    }
  }
})(window);
