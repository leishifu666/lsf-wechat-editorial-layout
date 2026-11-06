const form = document.querySelector('#style-selection');
const panels = [...document.querySelectorAll('[data-effect]')];
const intro = document.querySelector('[data-intro-wordmark]');
const feedback = document.querySelector('#notes');
const copyStatus = document.querySelector('#copy-status');
const fallback = document.querySelector('#copy-fallback');
const presetForm = document.querySelector('#preset-form');
const presetName = document.querySelector('#preset-name');
const presetList = document.querySelector('#preset-list');
const presetStatus = document.querySelector('#preset-status');
const key = 'lsf-wechat-editorial-layout:named-presets-v1';
const groups = ['chapters', 'stickers', 'screenshot-background'];
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let renaming = null;

function paintSelections() {
  for (const panel of panels) {
    const selected = form.elements.namedItem(panel.dataset.effect);
    panel.hidden = selected?.value !== panel.dataset.option;
  }
}

for (const preview of form.querySelectorAll('[data-option-preview]')) {
  const choice = preview.closest('.choice').querySelector('input');
  for (const panel of panels.filter(panel => panel.dataset.effect === choice.name && panel.dataset.option === choice.value)) {
    if (choice.name === 'screenshot-background') {
      const artwork = panel.querySelector('.screenshot-background');
      const sample = artwork ? new Image() : document.createElement('span');
      sample.className = artwork ? 'background-sample' : 'background-sample background-sample-sunset';
      if (artwork) {
        sample.src = artwork.src;
        sample.alt = '';
      }
      preview.append(sample);
    } else {
      const sample = new Image();
      sample.alt = '';
      sample.src = panel.src;
      preview.append(sample);
    }
  }
}
const screenshot = document.querySelector('.screenshot-content');
if (screenshot) {
  const matchInset = () => {
    const inset = Math.min(screenshot.naturalWidth, screenshot.naturalHeight) * .08;
    document.documentElement.style.setProperty('--screenshot-inset', `${100 * inset / (screenshot.naturalWidth + 2 * inset)}%`);
  };
  if (screenshot.naturalWidth) matchInset();
  else screenshot.addEventListener('load', matchInset, { once: true });
}

form.addEventListener('input', event => {
  copyStatus.textContent = '';
  fallback.hidden = true;
  const choice = event.target;
  if (choice.type !== 'radio') return;
  paintSelections();
  const target = document.getElementById(`preview-${choice.name}`);
  if (target && !reduced.matches) {
    target.getAnimations().forEach(animation => animation.cancel());
    target.animate([{opacity: .65}, {opacity: 1}], {duration: 220, easing: 'ease-out'});
  }
  if (target && matchMedia('(min-width: 900px)').matches) {
    const scrolling = target.closest('.reading-scroll');
    if (scrolling && scrolling.scrollHeight > scrolling.clientHeight + 4) {
      scrolling.scrollTo({top: target.getBoundingClientRect().top - scrolling.getBoundingClientRect().top
        + scrolling.scrollTop - 24, behavior: reduced.matches ? 'instant' : 'smooth'});
    }
  }
});

function readPresets() {
  try {
    const stored = JSON.parse(localStorage.getItem(key) || '[]');
    return Array.isArray(stored) ? stored.filter(item => typeof item?.id === 'string'
      && typeof item?.name === 'string' && item.selection && item.intro) : [];
  } catch {
    return [];
  }
}

function storePresets(presets) {
  try {
    localStorage.setItem(key, JSON.stringify(presets));
    return true;
  } catch {
    presetStatus.textContent = '浏览器无法保存预设，请检查储存空间';
    return false;
  }
}

function makeButton(label, action, className) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = label;
  if (className) button.className = className;
  button.addEventListener('click', action);
  return button;
}

function renderPresets() {
  presetList.replaceChildren();
  for (const item of readPresets()) {
    const row = document.createElement('li');
    row.className = 'preset-row';
    const apply = makeButton(item.name, () => {
      for (const group of groups) {
        const choice = [...form.querySelectorAll(`input[name="${group}"]`)]
          .find(input => input.value === item.selection[group]);
        if (choice) choice.checked = true;
      }
      intro.dispatchEvent(new CustomEvent('restore-intro-state', { detail: item.intro }));
      paintSelections();
      presetStatus.textContent = `已套用「${item.name}」`;
      copyStatus.textContent = '';
      fallback.hidden = true;
    }, 'preset-apply');
    apply.setAttribute('aria-label', `套用 ${item.name}`);
    const edit = makeButton('改名', () => {
      renaming = item.id;
      presetName.value = item.name;
      presetForm.querySelector('button').textContent = '确认改名';
      presetName.focus();
      presetName.select();
    });
    edit.setAttribute('aria-label', `改名 ${item.name}`);
    const remove = makeButton('删除', () => {
      if (remove.dataset.confirm !== 'true') {
        remove.textContent = '确认删除';
        remove.dataset.confirm = 'true';
        remove.addEventListener('blur', () => {
          remove.textContent = '删除';
          delete remove.dataset.confirm;
        }, { once: true });
        return;
      }
      if (storePresets(readPresets().filter(other => other.id !== item.id))) {
        if (renaming === item.id) resetPresetForm();
        renderPresets();
        presetStatus.textContent = `已删除「${item.name}」`;
      }
    });
    remove.setAttribute('aria-label', `删除 ${item.name}`);
    row.append(apply, edit, remove);
    presetList.append(row);
  }
}

function resetPresetForm() {
  renaming = null;
  presetForm.reset();
  presetForm.querySelector('button').textContent = '保存预设';
}

presetForm?.addEventListener('submit', event => {
  event.preventDefault();
  const name = presetName.value.trim();
  if (!name) {
    presetStatus.textContent = '请填写预设名称';
    presetName.focus();
    return;
  }
  const presets = readPresets();
  if (presets.some(item => item.name === name && item.id !== renaming)) {
    presetStatus.textContent = '已有同名预设，请换个名字';
    return;
  }
  const existing = presets.find(item => item.id === renaming);
  if (existing) {
    existing.name = name;
  } else {
    const state = intro.readIntroState?.();
    if (!state) {
      presetStatus.textContent = '样式仍在加载，请稍后再试';
      return;
    }
    const selection = Object.fromEntries(groups.map(group => [group, form.elements.namedItem(group).value]));
    presets.push({ id: crypto.randomUUID?.() ?? String(Date.now()), name, selection, intro: state });
  }
  if (!storePresets(presets)) return;
  presetStatus.textContent = `已${existing ? '改名为' : '保存'}「${name}」`;
  resetPresetForm();
  renderPresets();
});
presetForm?.addEventListener('keydown', event => {
  if (event.key === 'Escape' && renaming) resetPresetForm();
});
addEventListener('storage', event => {
  if (presetList && event.key === key) renderPresets();
});
if (presetList) renderPresets();
paintSelections();

form.addEventListener('submit', async event => {
  event.preventDefault();
  const lines = [];
  for (const group of form.querySelectorAll('.style-group')) {
    const title = group.querySelector('legend').textContent;
    const selected = group.querySelector('input:checked');
    if (!selected) {
      copyStatus.textContent = `请先选择${title}`;
      return;
    }
    lines.push(`${title}：${selected.labels[0].querySelector('.choice-name').textContent}`);
    if (intro && group.contains(intro)) {
      const state = intro.readIntroState?.();
      const text = intro.querySelector('[data-intro-text]')?.value.trim();
      if (intro.dataset.articleWorkflow === 'deferred' && state?.source === 'article') {
        lines.push('开篇文案来源：Agent 提炼文章');
        if (text) {
          const scenes = state.articleDraft.split('\n').map(line => line.trim()).filter(Boolean).slice(0, 4);
          lines.push('开篇文案（已回填）：', ...(state.hasScenes ? scenes : scenes.slice(0, 1)));
        } else {
          const length = state.hasScenes ? '给 1–4 条短句，每行一句。' : '给 1 条短句。';
          lines.push(`开篇文案任务：根据我提供的当前文章，提炼与主题和所选动效匹配的简短开篇文案。${length}只返回文案，方便我粘贴回预览。如果还没有收到文章，先向我索取正文。`);
        }
      } else {
        lines.push(`署名文字：${text || intro.dataset.author}`);
      }
      if (selected.value === 'emboss' && intro.readIntroState?.()?.logoUrl) lines.push('浮雕 Logo：已在预览中上传');
    }
  }
  if (feedback.value.trim()) lines.push(`补充意见：${feedback.value.trim()}`);
  const summary = lines.join('\n');
  try {
    await navigator.clipboard.writeText(summary);
    copyStatus.textContent = '已复制，粘贴到对话即可';
  } catch {
    fallback.value = summary;
    fallback.hidden = false;
    fallback.select();
    if (document.execCommand('copy')) {
      fallback.hidden = true;
      copyStatus.textContent = '已复制，粘贴到对话即可';
    } else copyStatus.textContent = '文字已选中，可手动复制';
  }
});
