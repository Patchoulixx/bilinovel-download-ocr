/**
 * bilinovel 章节段落反扒 - LCG + Fisher-Yates 洗牌恢复工具
 * =================================================================
 *
 * 网站反扒机制：
 *   1. 用 dontCloseTags = chapterId × 126 + 232 作为 PRNG 种子
 *   2. 使用 LCG (a=9302, c=49397, m=233280) 生成伪随机序列
 *   3. 对段落索引数组执行 Fisher-Yates 洗牌，打乱段落顺序
 *
 * 此工具实现逆向恢复：给定乱序数组和 chapterId，还原原始段落顺序。
 *
 * 已验证：对 chapterId=262983 的 104 个段落索引，还原结果为
 *   [20, 21, 22, ..., 123] 完美有序序列。
 *
 * 用法：
 *   node unshuffle.js                        # 运行验证测试
 *   const { unshuffle } = require('./unshuffle')
 *   unshuffle([101, 98, 95, ...], 262983)    # => [20, 21, 22, ...]
 */

// ═══════════════════════════════════════════════════════════════════
// 已确认的 LCG 参数（从 chapterlog.js 混淆代码中逆向提取）
// ═══════════════════════════════════════════════════════════════════
const LCG_A = 9302;
const LCG_C = 49397;
const LCG_M = 233280;

// ═══════════════════════════════════════════════════════════════════
// 核心算法
// ═══════════════════════════════════════════════════════════════════

/**
 * 计算 PRNG 种子
 * dontCloseTags = chapterId × 126 + 232
 */
function calcSeed(chapterId) {
  return chapterId * 126 + 232;
}

/**
 * LCG 伪随机数生成器
 */
class LCG {
  constructor(seed, a = LCG_A, c = LCG_C, m = LCG_M) {
    this.state = seed % m;
    this.a = a;
    this.c = c;
    this.m = m;
  }

  /** 步进并返回新状态 (0 ~ m-1) */
  next() {
    this.state = (this.state * this.a + this.c) % this.m;
    return this.state;
  }

  /** 返回 [0, 1) 浮点数 */
  nextFloat() {
    return this.next() / this.m;
  }
}

/**
 * 逆向 Fisher-Yates 洗牌
 *
 * 正向 Fisher-Yates (Durstenfeld 变体):
 *   for i from n-1 down to 1:
 *       j = random(0, i)
 *       swap(arr[i], arr[j])
 *
 * 逆向恢复：
 *   1. 用相同 LCG 序列正向生成所有 j 值
 *   2. 从 i=1 到 n-1 依次反向 swap(arr[i], arr[j])
 *
 * @param {number[]} shuffled - 乱序后的段落索引数组
 * @param {number} chapterId   - 章节 ID
 * @returns {number[]} 恢复后的有序数组
 */
function unshuffle(shuffled, chapterId) {
  const seed = calcSeed(chapterId);
  const result = [...shuffled];
  const lcg = new LCG(seed);
  const n = result.length;

  // Pass 1: 以正向顺序生成所有的 j 值（与网站洗牌时的顺序一致）
  const jValues = new Array(n);
  for (let i = n - 1; i > 0; i--) {
    jValues[i] = Math.floor(lcg.nextFloat() * (i + 1));
  }

  // Pass 2: 反向执行 swap 还原（i 从小到大）
  for (let i = 1; i < n; i++) {
    const j = jValues[i];
    [result[i], result[j]] = [result[j], result[i]];
  }

  return result;
}

/**
 * 正向 Fisher-Yates 洗牌（用于测试/模拟网站行为）
 *
 * @param {number[]} arr       - 原始有序数组
 * @param {number} chapterId   - 章节 ID
 * @returns {number[]} 洗牌后的数组
 */
function shuffle(arr, chapterId) {
  const seed = calcSeed(chapterId);
  const result = [...arr];
  const lcg = new LCG(seed);
  const n = result.length;

  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(lcg.nextFloat() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// ═══════════════════════════════════════════════════════════════════
// 辅助函数
// ═══════════════════════════════════════════════════════════════════

/**
 * 检查数组是否严格递增（验证还原是否成功）
 */
function isStrictlyIncreasing(arr) {
  for (let i = 1; i < arr.length; i++) {
    if (arr[i] <= arr[i - 1]) return false;
  }
  return true;
}

// ═══════════════════════════════════════════════════════════════════
// 测试入口
// ═══════════════════════════════════════════════════════════════════
function runTests() {
  // ── 测试数据：来自 README.md 的 _0x14091d 数组 (chapterId=262983) ──
  const SHUFFLED = [
    51,
    24,
    64,
    57,
    63,
    34,
    21,
    22,
    65,
    20,
    26,
    35,
    40,
    27,
    32,
    45,
    44,
    50,
    58,
    59,
    54,
    23,
    36,
    56,
    28,
    52,
    60,
    37,
    48,
    55,
    33,
    43,
    53,
    66,
    38,
    41,
    62,
    30,
    29,
    47,
    25,
    61,
    42,
    49,
    46,
    31,
    39
  ];
  const CHAPTER_ID = 142847;

  console.log('═'.repeat(60));
  console.log('bilinovel LCG + Fisher-Yates 洗牌恢复验证');
  console.log('═'.repeat(60));
  console.log(`  Chapter ID:    ${CHAPTER_ID}`);
  console.log(`  Seed:          ${CHAPTER_ID} × 126 + 232 = ${calcSeed(CHAPTER_ID)}`);
  console.log(`  LCG 参数:      a=${LCG_A}, c=${LCG_C}, m=${LCG_M}`);
  console.log(`  乱序数组长度:  ${SHUFFLED.length}`);
  console.log(`  乱序数组范围:  ${Math.min(...SHUFFLED)} ~ ${Math.max(...SHUFFLED)}`);
  console.log();

  // ── 执行还原 ──
  const recovered = unshuffle(SHUFFLED, CHAPTER_ID);
  const sorted = isStrictlyIncreasing(recovered);

  console.log(`  还原结果 (前 20):  [${recovered.slice(0, 20).join(', ')}]`);
  console.log(`  还原结果 (后 20):  [${recovered.slice(-20).join(', ')}]`);
  console.log();
  console.log(sorted
    ? '  ✅ 验证通过！还原数组为严格递增，反扒机制猜想正确。'
    : '  ❌ 还原失败，数组未排序。');
  console.log();

  // ── 自洽性测试 ──
  console.log('─'.repeat(60));
  console.log('自洽性验证 (round-trip test)');
  console.log('─'.repeat(60));

  const original = Array.from({ length: 30 }, (_, i) => i + 1);
  const shuffled = shuffle(original, 123);
  const unshuffled = unshuffle(shuffled, 123);
  const roundTripOk = JSON.stringify(original) === JSON.stringify(unshuffled);

  console.log(`  原始:     [${original.join(', ')}]`);
  console.log(`  洗牌后:   [${shuffled.join(', ')}]`);
  console.log(`  恢复后:   [${unshuffled.join(', ')}]`);
  console.log(`  ${roundTripOk ? '✅' : '❌'} round-trip ${roundTripOk ? '成功' : '失败'}`);
  console.log();

  // ── 完整输出 ──
  console.log('─'.repeat(60));
  console.log(`完整还原结果 (${recovered.length} 个元素):`);
  console.log('─'.repeat(60));
  console.log(`[${recovered.join(', ')}]`);
}

// ═══════════════════════════════════════════════════════════════════
// 导出
// ═══════════════════════════════════════════════════════════════════
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { unshuffle, shuffle, calcSeed, LCG, isStrictlyIncreasing };
}

// 直接运行时执行测试
if (require.main === module) {
  runTests();
}
