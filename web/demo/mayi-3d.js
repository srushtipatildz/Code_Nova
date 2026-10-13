/**
 * MayI — 3D Holographic Neural Consent Shield & Interactive Physics
 * Engine: Three.js (WebGL, 60 FPS)
 * Palette: Deep Navy (#030712, #0b1536), Sky Blue (#38bdf8, #0ea5e9), Crisp White (#ffffff)
 */
(function (window) {
  'use strict';

  var PALETTE = {
    navyAbyss: 0x030712,
    navyDeep: 0x060d24,
    navyMid: 0x0b1536,
    skyBright: 0x38bdf8,
    skyCore: 0x0ea5e9,
    skyDeep: 0x0284c7,
    whiteCrisp: 0xffffff,
    emeraldPulse: 0x10b981,
    coralRevoke: 0xf43f5e
  };

  /**
   * Represents an interactive 3D Shield instance
   */
  function MayIShield(container, opts) {
    opts = opts || {};
    this.container = container;
    this.width = container.clientWidth || 360;
    this.height = container.clientHeight || 360;
    this.currentState = 'idle';
    this.wireframeOnly = false;
    this.shockwaves = [];
    this.isDragging = false;
    this.prevMouse = { x: 0, y: 0 };
    this.dragDelta = { x: 0, y: 0 };
    this.targetRotation = { x: 0, y: 0 };
    this.currentRotation = { x: 0, y: 0 };
    this.speedMultiplier = 1.0;

    this.initScene();
    this.createLights();
    this.createShieldGeometry();
    this.createOrbitRings();
    this.createNeuralCore();
    this.createSentinels();
    this.createParticleField();
    this.bindEvents();
    this.animate();
  }

  MayIShield.prototype.initScene = function () {
    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 0.1, 1000);
    this.camera.position.z = 7.5;

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.domElement.style.width = '100%';
    this.renderer.domElement.style.height = '100%';
    this.renderer.domElement.style.cursor = 'grab';

    this.container.appendChild(this.renderer.domElement);

    this.rootGroup = new THREE.Group();
    this.scene.add(this.rootGroup);
  };

  MayIShield.prototype.createLights = function () {
    // Ambient deep navy illumination
    var ambient = new THREE.AmbientLight(PALETTE.navyMid, 2.2);
    this.scene.add(ambient);

    // Dynamic point light at center of the core
    this.coreLight = new THREE.PointLight(PALETTE.skyBright, 3.5, 14);
    this.coreLight.position.set(0, 0, 0);
    this.rootGroup.add(this.coreLight);

    // Directional rim lights for crisp specular edge reflections
    var dirLight1 = new THREE.DirectionalLight(PALETTE.whiteCrisp, 1.4);
    dirLight1.position.set(6, 6, 6);
    this.scene.add(dirLight1);

    var dirLight2 = new THREE.DirectionalLight(PALETTE.skyCore, 1.0);
    dirLight2.position.set(-6, -4, -4);
    this.scene.add(dirLight2);
  };

  MayIShield.prototype.createShieldGeometry = function () {
    this.shieldGroup = new THREE.Group();
    this.rootGroup.add(this.shieldGroup);

    // Outer Geodesic Icosahedron Cage
    var geo = new THREE.IcosahedronGeometry(2.35, 1);
    this.shieldMat = new THREE.MeshStandardMaterial({
      color: PALETTE.skyBright,
      emissive: PALETTE.skyDeep,
      emissiveIntensity: 0.25,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
      roughness: 0.1,
      metalness: 0.9
    });
    this.shieldMesh = new THREE.Mesh(geo, this.shieldMat);
    this.shieldGroup.add(this.shieldMesh);

    // Glowing Vertex Constellation Nodes
    var ptsGeo = new THREE.IcosahedronGeometry(2.36, 1);
    var ptsMat = new THREE.PointsMaterial({
      color: PALETTE.whiteCrisp,
      size: 0.08,
      transparent: true,
      opacity: 0.85
    });
    this.vertexPoints = new THREE.Points(ptsGeo, ptsMat);
    this.shieldGroup.add(this.vertexPoints);
  };

  MayIShield.prototype.createOrbitRings = function () {
    this.ringsGroup = new THREE.Group();
    this.rootGroup.add(this.ringsGroup);

    // Ring 1: Primary Gyroscope Ring (Sky Blue)
    var ring1Geo = new THREE.TorusGeometry(3.15, 0.035, 16, 120);
    var ring1Mat = new THREE.MeshStandardMaterial({
      color: PALETTE.skyBright,
      emissive: PALETTE.skyCore,
      emissiveIntensity: 0.6,
      roughness: 0.2,
      metalness: 0.9
    });
    this.ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    this.ringsGroup.add(this.ring1);

    // Ring 2: Polar Orthogonal Ring (Crisp White)
    var ring2Geo = new THREE.TorusGeometry(2.75, 0.025, 16, 120);
    var ring2Mat = new THREE.MeshStandardMaterial({
      color: PALETTE.whiteCrisp,
      emissive: PALETTE.skyBright,
      emissiveIntensity: 0.35,
      roughness: 0.1,
      metalness: 0.95
    });
    this.ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    this.ring2.rotation.x = Math.PI / 2.4;
    this.ring2.rotation.y = Math.PI / 4;
    this.ringsGroup.add(this.ring2);

    // Ring 3: Tilted Outer Sensor Ring
    var ring3Geo = new THREE.TorusGeometry(3.5, 0.015, 12, 100);
    var ring3Mat = new THREE.MeshBasicMaterial({
      color: PALETTE.skyBright,
      transparent: true,
      opacity: 0.35
    });
    this.ring3 = new THREE.Mesh(ring3Geo, ring3Mat);
    this.ring3.rotation.z = Math.PI / 3;
    this.ringsGroup.add(this.ring3);
  };

  MayIShield.prototype.createNeuralCore = function () {
    this.coreGroup = new THREE.Group();
    this.rootGroup.add(this.coreGroup);

    // Faceted Crystal Polyhedron (Local AI Neural Core)
    var crystalGeo = new THREE.OctahedronGeometry(1.22, 0);
    this.crystalMat = new THREE.MeshPhysicalMaterial({
      color: PALETTE.skyCore,
      emissive: PALETTE.skyDeep,
      emissiveIntensity: 0.55,
      roughness: 0.15,
      metalness: 0.75,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
      flatShading: true,
      transparent: true,
      opacity: 0.82
    });
    this.crystalMesh = new THREE.Mesh(crystalGeo, this.crystalMat);
    this.coreGroup.add(this.crystalMesh);

    // Inner Luminous Core
    var innerGeo = new THREE.IcosahedronGeometry(0.68, 0);
    this.innerMat = new THREE.MeshBasicMaterial({
      color: PALETTE.whiteCrisp,
      wireframe: true
    });
    this.innerMesh = new THREE.Mesh(innerGeo, this.innerMat);
    this.coreGroup.add(this.innerMesh);
  };

  MayIShield.prototype.createSentinels = function () {
    this.sentinels = [];
    this.sentinelGroup = new THREE.Group();
    this.rootGroup.add(this.sentinelGroup);

    var nodesConfig = [
      { name: 'Identity', color: PALETTE.skyBright, radius: 3.65, speed: 1.1, phase: 0 },
      { name: 'ConsentLedger', color: PALETTE.whiteCrisp, radius: 3.3, speed: 1.4, phase: Math.PI * 0.5 },
      { name: 'LocalQwenAI', color: PALETTE.emeraldPulse, radius: 3.9, speed: 0.9, phase: Math.PI },
      { name: 'RevokeSwitch', color: PALETTE.skyCore, radius: 2.95, speed: 1.6, phase: Math.PI * 1.5 }
    ];

    var sphereGeo = new THREE.SphereGeometry(0.12, 16, 16);

    for (var i = 0; i < nodesConfig.length; i++) {
      var cfg = nodesConfig[i];
      var mat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        emissive: cfg.color,
        emissiveIntensity: 0.8,
        roughness: 0.2,
        metalness: 0.8
      });
      var mesh = new THREE.Mesh(sphereGeo, mat);
      this.sentinelGroup.add(mesh);
      this.sentinels.push({
        mesh: mesh,
        cfg: cfg
      });
    }
  };

  MayIShield.prototype.createParticleField = function () {
    var count = 380;
    var positions = new Float32Array(count * 3);

    for (var i = 0; i < count; i++) {
      var rad = 4.2 + Math.random() * 4.5;
      var theta = Math.random() * Math.PI * 2;
      var phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = rad * Math.cos(phi);
    }

    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    var mat = new THREE.PointsMaterial({
      color: PALETTE.skyBright,
      size: 0.05,
      transparent: true,
      opacity: 0.55
    });

    this.particles = new THREE.Points(geo, mat);
    this.rootGroup.add(this.particles);
  };

  MayIShield.prototype.triggerPulse = function (intensityColor) {
    var ringGeo = new THREE.RingGeometry(0.1, 0.2, 32);
    var ringMat = new THREE.MeshBasicMaterial({
      color: intensityColor || PALETTE.skyBright,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.95
    });
    var shockwave = new THREE.Mesh(ringGeo, ringMat);
    shockwave.rotation.x = Math.PI / 2;
    this.rootGroup.add(shockwave);

    this.shockwaves.push({
      mesh: shockwave,
      scale: 1,
      opacity: 0.95
    });

    // Momentary burst on core light
    if (this.coreLight) {
      this.coreLight.intensity = 7.0;
    }
  };

  MayIShield.prototype.toggleWireframe = function () {
    this.wireframeOnly = !this.wireframeOnly;
    if (this.crystalMat) {
      this.crystalMat.wireframe = this.wireframeOnly;
    }
    return this.wireframeOnly;
  };

  MayIShield.prototype.resetView = function () {
    this.targetRotation.x = 0;
    this.targetRotation.y = 0;
    this.dragDelta.x = 0;
    this.dragDelta.y = 0;
    this.speedMultiplier = 1.0;
    this.triggerPulse(PALETTE.whiteCrisp);
  };

  MayIShield.prototype.setState = function (state) {
    this.currentState = state;
    if (state === 'verifying') {
      this.speedMultiplier = 2.4;
      this.coreLight.color.setHex(PALETTE.skyBright);
      this.crystalMat.emissive.setHex(PALETTE.skyCore);
      this.triggerPulse(PALETTE.skyBright);
    } else if (state === 'blessed') {
      this.speedMultiplier = 1.6;
      this.coreLight.color.setHex(PALETTE.emeraldPulse);
      this.crystalMat.emissive.setHex(PALETTE.emeraldPulse);
      this.triggerPulse(PALETTE.emeraldPulse);
    } else if (state === 'revoked') {
      this.speedMultiplier = 0.5;
      this.coreLight.color.setHex(PALETTE.coralRevoke);
      this.crystalMat.emissive.setHex(PALETTE.coralRevoke);
      this.triggerPulse(PALETTE.coralRevoke);
    } else {
      this.speedMultiplier = 1.0;
      this.coreLight.color.setHex(PALETTE.skyBright);
      this.crystalMat.emissive.setHex(PALETTE.skyDeep);
      this.triggerPulse(PALETTE.skyBright);
    }
  };

  MayIShield.prototype.bindEvents = function () {
    var self = this;
    var dom = this.renderer.domElement;

    // Window Resize
    window.addEventListener('resize', function () {
      self.width = self.container.clientWidth || 360;
      self.height = self.container.clientHeight || 360;
      self.camera.aspect = self.width / self.height;
      self.camera.updateProjectionMatrix();
      self.renderer.setSize(self.width, self.height);
    });

    // Pointer Parallax & Drag Rotation
    dom.addEventListener('pointerdown', function (e) {
      self.isDragging = true;
      self.prevMouse.x = e.clientX;
      self.prevMouse.y = e.clientY;
      dom.style.cursor = 'grabbing';
    });

    window.addEventListener('pointermove', function (e) {
      var rect = dom.getBoundingClientRect();
      var inView = (
        e.clientX >= rect.left && e.clientX <= rect.right &&
        e.clientY >= rect.top && e.clientY <= rect.bottom
      );

      if (self.isDragging) {
        var dx = e.clientX - self.prevMouse.x;
        var dy = e.clientY - self.prevMouse.y;
        self.dragDelta.x += dx * 0.007;
        self.dragDelta.y += dy * 0.007;
        self.prevMouse.x = e.clientX;
        self.prevMouse.y = e.clientY;
      } else if (inView) {
        // Subtle mouse parallax
        var normX = ((e.clientX - rect.left) / self.width) * 2 - 1;
        var normY = -(((e.clientY - rect.top) / self.height) * 2 - 1);
        self.targetRotation.y = normX * 0.45;
        self.targetRotation.x = -normY * 0.35;
      }
    });

    window.addEventListener('pointerup', function () {
      if (self.isDragging) {
        self.isDragging = false;
        dom.style.cursor = 'grab';
      }
    });

    // Click to pulse
    dom.addEventListener('click', function () {
      self.triggerPulse(PALETTE.whiteCrisp);
    });
  };

  MayIShield.prototype.animate = function () {
    var self = this;
    var clock = new THREE.Clock();

    function renderLoop() {
      requestAnimationFrame(renderLoop);
      var delta = clock.getDelta();
      var time = clock.getElapsedTime() * self.speedMultiplier;

      // Inertia & drag rotation damping
      self.dragDelta.x *= 0.94;
      self.dragDelta.y *= 0.94;
      self.targetRotation.y += self.dragDelta.x;
      self.targetRotation.x += self.dragDelta.y;

      // Lerp root group towards target rotation
      self.currentRotation.x += (self.targetRotation.x - self.currentRotation.x) * 0.07;
      self.currentRotation.y += (self.targetRotation.y - self.currentRotation.y) * 0.07;
      self.rootGroup.rotation.x = self.currentRotation.x;
      self.rootGroup.rotation.y = self.currentRotation.y;

      // Intrinsic rotation
      if (self.shieldGroup) {
        self.shieldGroup.rotation.y += 0.0035 * self.speedMultiplier;
        self.shieldGroup.rotation.x += 0.0018 * self.speedMultiplier;
      }

      if (self.ring1) {
        self.ring1.rotation.z += 0.006 * self.speedMultiplier;
        self.ring1.rotation.y += 0.004 * self.speedMultiplier;
      }

      if (self.ring2) {
        self.ring2.rotation.x -= 0.008 * self.speedMultiplier;
        self.ring2.rotation.z += 0.005 * self.speedMultiplier;
      }

      if (self.ring3) {
        self.ring3.rotation.z -= 0.003 * self.speedMultiplier;
      }

      if (self.coreGroup) {
        self.coreGroup.rotation.y += 0.012 * self.speedMultiplier;
        self.coreGroup.rotation.z += 0.007 * self.speedMultiplier;

        // Neural breath scaling
        var pulseScale = 1.0 + Math.sin(time * 3.0) * 0.06;
        self.coreGroup.scale.set(pulseScale, pulseScale, pulseScale);
      }

      if (self.particles) {
        self.particles.rotation.y -= 0.001 * self.speedMultiplier;
      }

      // Smooth light decay back to base
      if (self.coreLight && self.coreLight.intensity > 3.5) {
        self.coreLight.intensity -= delta * 5.0;
        if (self.coreLight.intensity < 3.5) self.coreLight.intensity = 3.5;
      }

      // Animate Sentinel Orbits
      if (self.sentinels) {
        for (var i = 0; i < self.sentinels.length; i++) {
          var s = self.sentinels[i];
          var angle = time * s.cfg.speed + s.cfg.phase;
          var r = s.cfg.radius;
          s.mesh.position.x = Math.cos(angle) * r;
          s.mesh.position.y = Math.sin(angle * 1.5) * 0.45;
          s.mesh.position.z = Math.sin(angle) * r;
        }
      }

      // Animate shockwaves
      for (var j = self.shockwaves.length - 1; j >= 0; j--) {
        var sw = self.shockwaves[j];
        sw.scale += delta * 7.5;
        sw.opacity -= delta * 1.2;
        sw.mesh.scale.set(sw.scale, sw.scale, sw.scale);
        sw.mesh.material.opacity = Math.max(0, sw.opacity);

        if (sw.opacity <= 0) {
          self.rootGroup.remove(sw.mesh);
          self.shockwaves.splice(j, 1);
        }
      }

      self.renderer.render(self.scene, self.camera);
    }

    renderLoop();
  };

  /**
   * High-End 3D Card Tilt & Specular Physics
   */
  function init3DCardPhysics() {
    var selector = '.card, .agent, .rm-col, .rcell, .host-banner, .step';
    var cards = document.querySelectorAll(selector);

    cards.forEach(function (card) {
      if (card.dataset.tiltInitialized) return;
      card.dataset.tiltInitialized = 'true';

      card.style.transformStyle = 'preserve-3d';
      card.style.transition = 'transform 0.15s ease-out, box-shadow 0.25s ease, border-color 0.25s ease';

      card.addEventListener('pointermove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;

        var normX = (x / rect.width) * 2 - 1;
        var normY = (y / rect.height) * 2 - 1;

        var rotX = -normY * 8.5; // max ±8.5 deg
        var rotY = normX * 8.5;

        card.style.transform =
          'perspective(900px) rotateX(' + rotX.toFixed(2) + 'deg) rotateY(' + rotY.toFixed(2) + 'deg) translateY(-5px) scale3d(1.018, 1.018, 1.018)';
        
        // Specular highlight CSS variable
        var pctX = Math.round((x / rect.width) * 100);
        var pctY = Math.round((y / rect.height) * 100);
        card.style.setProperty('--mouse-x', pctX + '%');
        card.style.setProperty('--mouse-y', pctY + '%');
      });

      card.addEventListener('pointerleave', function () {
        card.style.transition = 'transform 0.45s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease';
        card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0px) scale3d(1, 1, 1)';
      });
    });
  }

  // Global Export
  window.MayI3D = {
    Shield: MayIShield,
    activeInstances: [],
    initCardPhysics: init3DCardPhysics,
    create: function (containerOrId, opts) {
      var container = typeof containerOrId === 'string'
        ? document.getElementById(containerOrId)
        : containerOrId;
      if (!container) return null;
      var inst = new MayIShield(container, opts);
      this.activeInstances.push(inst);
      return inst;
    },
    setState: function (state) {
      this.activeInstances.forEach(function (inst) {
        inst.setState(state);
      });
    },
    triggerPulse: function (color) {
      this.activeInstances.forEach(function (inst) {
        inst.triggerPulse(color);
      });
    }
  };

  // Auto-init cards on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function () {
    setTimeout(init3DCardPhysics, 250);

    // Watch for dynamic cards injected by app.js
    var observer = new MutationObserver(function () {
      init3DCardPhysics();
    });
    var stage = document.getElementById('stage') || document.body;
    if (stage) {
      observer.observe(stage, { childList: true, subtree: true });
    }
  });

})(window);
