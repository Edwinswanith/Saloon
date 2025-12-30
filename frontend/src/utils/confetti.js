/**
 * Confetti celebration utility using canvas-confetti
 */
import confetti from 'canvas-confetti';

/**
 * Trigger a success celebration with confetti
 * @param {object} options - Confetti options
 */
export const celebrateSuccess = (options = {}) => {
  const defaults = {
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 },
    colors: ['#d4a574', '#c89960', '#3b82f6', '#10b981', '#f59e0b']
  };

  confetti({
    ...defaults,
    ...options
  });
};

/**
 * Trigger a big celebration (for major wins)
 */
export const celebrateBig = () => {
  const count = 200;
  const defaults = {
    origin: { y: 0.7 },
    colors: ['#d4a574', '#c89960', '#3b82f6', '#10b981', '#f59e0b', '#ec4899']
  };

  function fire(particleRatio, opts) {
    confetti({
      ...defaults,
      ...opts,
      particleCount: Math.floor(count * particleRatio)
    });
  }

  fire(0.25, {
    spread: 26,
    startVelocity: 55,
  });
  fire(0.2, {
    spread: 60,
  });
  fire(0.35, {
    spread: 100,
    decay: 0.91,
    scalar: 0.8
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 25,
    decay: 0.92,
    scalar: 1.2
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 45,
  });
};

/**
 * Trigger confetti from a specific element
 * @param {HTMLElement} element - The element to shoot confetti from
 */
export const celebrateFrom = (element) => {
  if (!element) return;
  
  const rect = element.getBoundingClientRect();
  const x = (rect.left + rect.width / 2) / window.innerWidth;
  const y = (rect.top + rect.height / 2) / window.innerHeight;

  confetti({
    particleCount: 50,
    spread: 60,
    origin: { x, y },
    colors: ['#d4a574', '#c89960', '#3b82f6', '#10b981']
  });
};

/**
 * Continuous confetti for extra special occasions
 * @param {number} duration - Duration in milliseconds
 */
export const celebrateContinuous = (duration = 3000) => {
  const end = Date.now() + duration;
  const colors = ['#d4a574', '#c89960', '#3b82f6', '#10b981', '#f59e0b'];

  (function frame() {
    confetti({
      particleCount: 2,
      angle: 60,
      spread: 55,
      origin: { x: 0 },
      colors: colors
    });
    confetti({
      particleCount: 2,
      angle: 120,
      spread: 55,
      origin: { x: 1 },
      colors: colors
    });

    if (Date.now() < end) {
      requestAnimationFrame(frame);
    }
  }());
};

export default {
  celebrateSuccess,
  celebrateBig,
  celebrateFrom,
  celebrateContinuous
};

