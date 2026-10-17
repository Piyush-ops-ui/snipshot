import { ReelIR } from '../types/reel_ir';

export const SAMPLE_REEL: ReelIR = {
  schema_version: '1.0.0',
  reel_id: 'reel_py_async_001',
  mode: 'mode_a_extract',
  title: 'Python Async Context Managers & Resource Cleanup',
  source_media_path: '/media/lectures/python_async_resource_management.mp4',
  clip_start: 114.2,
  clip_end: 154.8,
  total_duration: 40.6,
  audio_path: '/audio/python_async_clean.wav',
  pedagogical_score: 9.6,
  error_resolved_at: 23.4,
  entry_closure_verified: true,
  exit_closure_verified: true,
  technical_term_count: 5,
  created_at: new Date().toISOString(),
  typing_hyperlapse_intervals: [[14.0, 18.5]],
  template_archetype: 'bug_hunter',
  brand_kit: {
    id: 'brand_perpetual_cyan',
    name: 'SnipShot Obsidian Cyan',
    primary_color: '#00F2FE',
    secondary_color: '#4FACFE',
    background_color: '#0B0F17',
    text_color: '#F8FAFC',
    font_family: 'JetBrains Mono',
    font_size_pt: 32,
    logo_position: 'top_right',
    show_provenance_badge: true,
    enable_intro_bumper: false,
    intro_bumper_duration: 1.5,
    enable_outro_bumper: true,
    outro_bumper_duration: 2.0,
    watermark_text: 'SnipShot Perpetual Studio',
  },
  redaction_boxes: [
    {
      id: 'redact_1',
      start: 5.0,
      end: 35.0,
      bbox: [720, 28, 260, 36],
      secret_type: 'api_key',
      confidence: 0.99,
    },
  ],
  viewports: [
    {
      timestamp: 0.0,
      mode: 'split_stage',
      top_crop: [120, 40, 480, 480],
      bottom_crop: [40, 240, 1020, 720],
      transition_duration: 0.3,
    },
    {
      timestamp: 16.5,
      mode: 'single_focus',
      top_crop: [180, 220, 920, 680],
      transition_duration: 0.25,
    },
  ],
  code_cards: [
    {
      id: 'card_1',
      start: 18.5,
      end: 38.0,
      language: 'python',
      code: `async with get_db_session() as session:
    result = await session.execute(query)
    return result.scalars().all()`,
      active_line_indices: [1, 2, 3],
      verified_by_ast: true,
    },
  ],
  transcript: [
    { id: 'w1', word: 'When', start: 0.0, end: 0.3, confidence: 0.99, is_technical: false },
    { id: 'w2', word: 'you', start: 0.3, end: 0.5, confidence: 0.99, is_technical: false },
    { id: 'w3', word: 'open', start: 0.5, end: 0.8, confidence: 0.98, is_technical: false },
    {
      id: 'w4',
      word: 'async_session',
      start: 0.8,
      end: 1.6,
      confidence: 0.98,
      is_technical: true,
      raw_asr_word: 'a sink session',
      provenance_frame_time: 12.4,
      provenance_bbox: [420, 180, 260, 48],
      provenance_thumbnail_url: '/provenance/crop_1.png',
    },
    { id: 'w5', word: 'without', start: 1.6, end: 2.0, confidence: 0.97, is_technical: false },
    { id: 'w6', word: 'a', start: 2.0, end: 2.1, confidence: 0.99, is_technical: false },
    { id: 'w7', word: 'context', start: 2.1, end: 2.6, confidence: 0.99, is_technical: false },
    { id: 'w8', word: 'manager,', start: 2.6, end: 3.3, confidence: 0.96, is_technical: false },
    { id: 'w9', word: 'connection', start: 3.5, end: 3.9, confidence: 0.98, is_technical: false },
    { id: 'w10', word: 'pools', start: 3.9, end: 4.2, confidence: 0.97, is_technical: false },
    { id: 'w11', word: 'exhaust.', start: 4.2, end: 4.7, confidence: 0.98, is_technical: false },
    { id: 'w12', word: 'Always', start: 4.7, end: 5.1, confidence: 0.98, is_technical: false },
    { id: 'w13', word: 'use', start: 5.1, end: 5.5, confidence: 0.95, is_technical: false },
    {
      id: 'w14',
      word: 'asynccontextmanager',
      start: 5.5,
      end: 6.8,
      confidence: 0.98,
      is_technical: true,
      raw_asr_word: 'a sink context manager',
      provenance_frame_time: 13.5,
      provenance_bbox: [460, 310, 310, 48],
      provenance_thumbnail_url: '/provenance/crop_2.png',
    },
    { id: 'w15', word: 'to', start: 7.2, end: 7.6, confidence: 0.99, is_technical: false },
    { id: 'w16', word: 'guarantee', start: 7.6, end: 7.8, confidence: 0.99, is_technical: false },
    { id: 'w17', word: 'automatic', start: 7.8, end: 8.5, confidence: 0.98, is_technical: false },
    { id: 'w18', word: 'cleanup.', start: 8.5, end: 9.3, confidence: 0.98, is_technical: false },
  ],
  growth_pack: {
    hook_title: 'Prevent Database Connection Leaks with Async Context Managers ⚡',
    broad_hashtags: ['#coding', '#programming', '#softwareengineering', '#backend'],
    stack_hashtags: ['#python', '#fastapi', '#sqlalchemy', '#asyncio'],
    micro_api_hashtags: ['#contextmanager', '#asyncwith', '#connectionpool', '#dboptimization'],
    pinned_code_comment: `⚡ Always use an async context manager to ensure database connections are released immediately back to the pool:

\`\`\`python
async with get_db_session() as session:
    result = await session.execute(query)
    return result.scalars().all()
\`\`\`

Full production test suite and architectural cheat sheet linked in bio! 🚀`,
    qr_code_data: 'https://github.com/snipshot/clean-architecture-guide',
  },
};
