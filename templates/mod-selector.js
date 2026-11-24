(function () {
  var MODS = [
    'NM','HD','HR','DT','NC','HT','FL','EZ','NF','SD','PF','RX','AP','V2','DA','CS',
    'WU','WD','AT','RE','PR','TC','MR','RD','AD','FR','MU','SY','RV6'
  ];

  var style = document.createElement('style');
  style.textContent = `
    .mod-selector { position:relative; min-width:220px; }
    .mod-selector-button {
      width:100%; min-height:38px; display:flex; align-items:center; justify-content:space-between;
      gap:10px; padding:8px 10px; border-radius:8px; background:#161c27;
      border:1px solid rgba(93,142,240,0.25); color:#dde2ec; cursor:pointer;
    }
    .mod-selector-panel {
      display:none; position:absolute; z-index:60; top:calc(100% + 6px); left:0;
      width:360px; max-height:460px; overflow:auto; padding:10px;
      border-radius:12px; background:#1e2535; border:1px solid rgba(93,142,240,0.25);
      box-shadow:0 16px 40px rgba(0,0,0,0.55);
    }
    .mod-selector.open .mod-selector-panel { display:block; }
    .mod-selector-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:6px; }
    .mod-selector-option { cursor:pointer; user-select:none; }
    .mod-selector-option input { display:none; }
    .mod-selector-option span {
      display:block; text-align:center; padding:6px 4px; border-radius:8px;
      background:#161c27; color:rgba(221,226,236,0.55); border:1px solid rgba(93,142,240,0.15);
      font-size:12px; font-weight:700;
    }
    .mod-selector-option input:checked + span {
      background:rgba(93,142,240,0.2); color:#5b8ef0; border-color:#5b8ef0;
    }
    .mod-selector-settings {
      margin-top:10px; padding-top:10px; border-top:1px solid rgba(93,142,240,0.12);
    }
    .mod-selector-setting-group {
      display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px;
      margin-top:8px;
    }
    .mod-selector-setting-group.hidden { display:none; }
    .mod-selector-settings input, .mod-selector-settings select {
      width:100%; box-sizing:border-box; margin-top:4px; padding:7px 8px; border-radius:7px;
      background:#161c27; border:1px solid rgba(93,142,240,0.2); color:#dde2ec;
    }
  `;
  document.head.appendChild(style);

  function numberValue(input) {
    if (!input || input.value === '') return null;
    var value = Number(input.value);
    return Number.isFinite(value) ? value : null;
  }

  function setting(container, key) {
    return container.querySelector('[data-setting="' + key + '"]');
  }

  function checkedSetting(container, key) {
    var input = setting(container, key);
    return input ? input.checked : false;
  }

  function collect(container) {
    var entries = [];
    container.querySelectorAll('.mod-selector-option input:checked').forEach(function (input) {
      var entry = { acronym: input.value };
      var settings = {};

      if (input.value === 'HD' && checkedSetting(container, 'hd-only-fade')) {
        settings.isOnlyFadeApproachCircles = true;
      }
      if (input.value === 'FL') {
        var followDelay = numberValue(setting(container, 'fl-follow-delay'));
        if (followDelay !== null) settings.areaFollowDelay = followDelay;
      }
      if (input.value === 'DA') {
        ['ar','cs','od','hp'].forEach(function (key) {
          var value = numberValue(setting(container, 'da-' + key));
          if (value !== null) settings[key] = { original: value, adjusted: value };
        });
      }
      if (input.value === 'CS') {
        var rate = numberValue(setting(container, 'cs-rate'));
        if (rate !== null) settings.rateMultiplier = rate;
      }
      if (input.value === 'WU') {
        var wuInitial = numberValue(setting(container, 'wu-initial'));
        var wuFinal = numberValue(setting(container, 'wu-final'));
        if (wuInitial !== null) settings.initialRate = wuInitial;
        if (wuFinal !== null) settings.finalRate = wuFinal;
      }
      if (input.value === 'WD') {
        var wdInitial = numberValue(setting(container, 'wd-initial'));
        var wdFinal = numberValue(setting(container, 'wd-final'));
        if (wdInitial !== null) settings.initialRate = wdInitial;
        if (wdFinal !== null) settings.finalRate = wdFinal;
      }
      if (input.value === 'MU') {
        if (checkedSetting(container, 'mu-inverse')) settings.inverseMuting = true;
        if (checkedSetting(container, 'mu-metronome')) settings.enableMetronome = true;
        var combo = numberValue(setting(container, 'mu-combo'));
        if (combo !== null) settings.muteComboCount = combo;
        if (checkedSetting(container, 'mu-hit-sounds')) settings.affectsHitSounds = true;
      }
      if (input.value === 'MR') {
        var axes = numberValue(setting(container, 'mr-axes'));
        if (axes !== null) settings.flippedAxes = axes;
      }
      if (input.value === 'AD') {
        var scale = numberValue(setting(container, 'ad-scale'));
        var styleValue = numberValue(setting(container, 'ad-style'));
        if (scale !== null) settings.scale = scale;
        if (styleValue !== null) settings.style = styleValue;
      }
      if (input.value === 'RD') {
        var seed = numberValue(setting(container, 'rd-seed'));
        var angle = numberValue(setting(container, 'rd-angle'));
        if (seed !== null) settings.seed = seed;
        if (angle !== null) settings.angleSharpness = angle;
      }

      if (Object.keys(settings).length) entry.settings = settings;
      entries.push(entry);
    });
    if (entries.length === 1 && entries[0].acronym === 'NM') return [];
    if (entries.length > 1) entries = entries.filter(function (entry) { return entry.acronym !== 'NM'; });
    return entries;
  }

  function acronyms(container) {
    return collect(container).map(function (entry) { return entry.acronym; });
  }

  function init(container) {
    if (container.dataset.initialized) return;
    container.dataset.initialized = 'true';
    var selected = (container.dataset.selected || '').split(',').map(function (value) {
      return value.trim().toUpperCase();
    }).filter(Boolean);

    var grid = MODS.map(function (mod) {
      var checked = selected.indexOf(mod) !== -1 ? ' checked' : '';
      return '<label class="mod-selector-option"><input type="checkbox" value="' + mod + '"' + checked +
        '><span>' + mod + '</span></label>';
    }).join('');

    container.innerHTML =
      '<button type="button" class="mod-selector-button"><span class="mod-selector-text">No mods</span><i class="fas fa-chevron-down text-xs"></i></button>' +
      '<div class="mod-selector-panel"><div class="mod-selector-grid">' + grid + '</div>' +
      '<div class="mod-selector-settings">' +
        '<div class="mod-selector-setting-group" data-mod-group="HD"><label class="text-xs"><input type="checkbox" data-setting="hd-only-fade"> Only fade approach circles</label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="FL"><label class="text-xs">Follow delay (0-1.2)<input type="number" step="0.12" min="0" max="1.2" data-setting="fl-follow-delay"></label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="DA">' +
          '<label class="text-xs">AR<input type="number" step="0.1" min="0" max="12.5" data-setting="da-ar"></label>' +
          '<label class="text-xs">CS<input type="number" step="0.1" min="0" max="15" data-setting="da-cs"></label>' +
          '<label class="text-xs">OD<input type="number" step="0.1" min="0" max="11" data-setting="da-od"></label>' +
          '<label class="text-xs">HP<input type="number" step="0.1" min="0" max="11" data-setting="da-hp"></label>' +
        '</div>' +
        '<div class="mod-selector-setting-group" data-mod-group="CS"><label class="text-xs">Rate multiplier (0.5-2.0)<input type="number" step="0.05" min="0.5" max="2" data-setting="cs-rate"></label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="WU"><label class="text-xs">Initial rate (0.5-1.95)<input type="number" step="0.05" min="0.5" max="1.95" data-setting="wu-initial"></label><label class="text-xs">Final rate (0.55-2.0)<input type="number" step="0.05" min="0.55" max="2" data-setting="wu-final"></label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="WD"><label class="text-xs">Initial rate (0.55-2.0)<input type="number" step="0.05" min="0.55" max="2" data-setting="wd-initial"></label><label class="text-xs">Final rate (0.5-1.95)<input type="number" step="0.05" min="0.5" max="1.95" data-setting="wd-final"></label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="MU"><label class="text-xs"><input type="checkbox" data-setting="mu-inverse"> Inverse muting</label><label class="text-xs"><input type="checkbox" data-setting="mu-metronome"> Enable metronome</label><label class="text-xs">Mute combo count<input type="number" min="0" max="500" step="1" data-setting="mu-combo"></label><label class="text-xs"><input type="checkbox" data-setting="mu-hit-sounds"> Affect hit sounds</label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="MR"><label class="text-xs">Flipped axes<select data-setting="mr-axes"><option value="">Default</option><option value="0">Horizontal</option><option value="1">Vertical</option><option value="2">Both</option></select></label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="AD"><label class="text-xs">Scale (1.5-10)<input type="number" step="0.1" min="1.5" max="10" data-setting="ad-scale"></label><label class="text-xs">Style<select data-setting="ad-style"><option value="">Linear</option><option value="1">Gravity</option><option value="2">In/Out 1</option><option value="3">In/Out 2</option><option value="4">Accelerate 1</option><option value="5">Accelerate 2</option><option value="6">Accelerate 3</option><option value="7">Decelerate 1</option><option value="8">Decelerate 2</option><option value="9">Decelerate 3</option><option value="10">Bounce In</option><option value="11">Bounce Out</option><option value="12">Bounce In/Out</option></select></label></div>' +
        '<div class="mod-selector-setting-group" data-mod-group="RD"><label class="text-xs">Seed (0-4294967295)<input type="number" min="0" max="4294967295" step="1" data-setting="rd-seed"></label><label class="text-xs">Angle sharpness (1-10)<input type="number" step="0.1" min="1" max="10" data-setting="rd-angle"></label></div>' +
      '</div></div>';

    var button = container.querySelector('.mod-selector-button');
    var text = container.querySelector('.mod-selector-text');

    function refresh() {
      var values = acronyms(container);
      text.textContent = values.length ? values.join(', ') : 'No mods';
      text.style.color = values.length ? '#5b8ef0' : '#dde2ec';
      container.querySelectorAll('[data-mod-group]').forEach(function (group) {
        var selectedInput = container.querySelector('.mod-selector-option input[value="' + group.dataset.modGroup + '"]');
        group.classList.toggle('hidden', !selectedInput || !selectedInput.checked);
      });
    }

    button.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      container.classList.toggle('open');
    });
    container.querySelectorAll('.mod-selector-option input').forEach(function (input) {
      input.addEventListener('change', function () {
        if (input.value === 'NM' && input.checked) {
          container.querySelectorAll('.mod-selector-option input:checked').forEach(function (other) {
            if (other !== input) other.checked = false;
          });
        } else if (input.checked) {
          var nm = container.querySelector('.mod-selector-option input[value="NM"]');
          if (nm) nm.checked = false;
        }
        refresh();
      });
    });
    container.querySelectorAll('.mod-selector-settings input, .mod-selector-settings select').forEach(function (input) {
      input.addEventListener('input', refresh);
      input.addEventListener('change', refresh);
    });
    document.addEventListener('click', function (event) {
      if (!container.contains(event.target)) container.classList.remove('open');
    });
    refresh();
  }

  window.ModSelector = { init: init, collect: collect, acronyms: acronyms };
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.mod-selector').forEach(init);
  });
})();
