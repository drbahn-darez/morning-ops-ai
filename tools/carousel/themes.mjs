// Brand themes for the carousel renderer. Colors and type follow each brand pack
// in .claude/skills/insta-growth/references/brands/.

export const THEMES = {
  ega: {
    handle: '', // set the real handle in brands/ega.md and pass it as spec.handle
    fonts:
      'https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700;900&family=Noto+Sans+KR:wght@400;500;700&family=Cormorant+Garamond:ital,wght@0,500;1,500&display=swap',
    bg: '#0A2A8C', // deep cobalt — first frame anchors the brand palette
    bgAlt: '#F4F1EA', // warm paper for alternating body slides
    ink: '#F7F5F0',
    inkAlt: '#0B1B4D',
    muted: 'rgba(247,245,240,0.68)',
    mutedAlt: 'rgba(11,27,77,0.62)',
    accent: '#9DB7FF',
    accentAlt: '#0A2A8C',
    families: ['Noto Serif KR', 'Noto Sans KR', 'Cormorant Garamond'],
    headline: "'Noto Serif KR', serif",
    body: "'Noto Sans KR', sans-serif",
    eyebrow: "'Cormorant Garamond', serif",
    eyebrowStyle: 'italic',
    eyebrowTracking: '0.06em',
    headlineWeight: 700,
    alternate: true,
  },
  adro: {
    handle: '@adro.inc',
    fonts:
      'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&family=Inter+Tight:wght@500;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap',
    bg: '#0B0B0C',
    bgAlt: '#0B0B0C',
    ink: '#FFFFFF',
    inkAlt: '#FFFFFF',
    muted: 'rgba(255,255,255,0.62)',
    mutedAlt: 'rgba(255,255,255,0.62)',
    accent: '#E1251B',
    accentAlt: '#E1251B',
    families: ['Inter Tight', 'Noto Sans KR', 'JetBrains Mono'],
    headline: "'Inter Tight', 'Noto Sans KR', sans-serif",
    body: "'Noto Sans KR', 'Inter Tight', sans-serif",
    eyebrow: "'JetBrains Mono', monospace",
    eyebrowStyle: 'normal',
    eyebrowTracking: '0.14em',
    headlineWeight: 900,
    alternate: false,
    grid: true, // faint engineering grid lines
  },
};

export const SIZES = {
  '4:5': { width: 1080, height: 1350 },
  '3:4': { width: 1080, height: 1440 },
  '1:1': { width: 1080, height: 1080 },
  '9:16': { width: 1080, height: 1920 }, // Reels cover image (cover_url)
};
