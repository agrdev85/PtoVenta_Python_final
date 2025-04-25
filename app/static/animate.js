const animations = [
    'animate__bounce',
    'animate__pulse',
    'animate__rubberBand',
    'animate__swing',
    'animate__tada',
    'animate__jello',
    'animate__heartBeat',
    'animate__wobble',
    'animate__flip'
  ];
  
  function animateLogo() {
    const logo = document.getElementById('logoAnimated');
    const randomAnim = animations[Math.floor(Math.random() * animations.length)];
  
    logo.classList.remove(...logo.classList); // remove all classes
    logo.classList.add('animate__animated', randomAnim);
  
    // Remove animation classes after it ends
    logo.addEventListener('animationend', () => {
      logo.classList.remove('animate__animated', randomAnim);
    }, { once: true });
  }
  
  // Animate every 5 seconds
  setInterval(animateLogo, 5000);
  
  // Initial animation
  animateLogo();