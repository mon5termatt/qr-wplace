#!/usr/bin/env python3
import io
from typing import Optional, Tuple

from flask import Flask, render_template_string, request, send_file, jsonify, Response
import re
import hashlib


app = Flask(__name__)


PAGE = r"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>QR Generator for Wplace</title>
    <meta name="description" content="Minimal QR code generator (starts at 21x21). Live preview, no fluff." />
    <meta name="theme-color" content="#000000" />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="Minimal QR Generator" />
    <meta property="og:description" content="Generate the smallest QR codes (min 21x21). Live, configurable, downloadable." />
    <meta property="og:url" content="{{ request.url_root }}" />
    <meta property="og:image" content="/favicon.svg" />
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content="Minimal QR Generator" />
    <meta name="twitter:description" content="Generate tiny QR codes (21x21+), live preview, download." />
    <style>
      :root { color-scheme: light dark; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; padding: 24px; max-width: 820px; margin: 0 auto; line-height: 1.45; }
      main { max-width: 820px; margin: 0 auto; padding: 24px; }
      header { display: grid; place-items: center; gap: 12px; text-align: center; color: #fff; width: 100vw; margin-left: calc(50% - 50vw); max-height: 128px; background: #000; padding: 12px 0; }
      header a { color: inherit; }
      .brand-logo { max-width: 90vw; max-height: 128px; height: auto; display: block; image-rendering: -webkit-optimize-contrast; }
      .tag { opacity: 0.9; font-size: 14px; }
      form { display: grid; gap: 12px; grid-template-columns: 1fr; align-items: center; }
      label { display: grid; gap: 6px; }
      .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
      .controls { display: grid; gap: 12px; }
      input[type=text] { padding: 10px 12px; font-size: 16px; border: 1px solid #ccc; border-radius: 8px; }
      input[type=color] { width: 42px; height: 36px; padding: 0; border: 1px solid #ccc; border-radius: 6px; }
      input[type=range] { width: 180px; }
      button { padding: 10px 14px; font-size: 16px; cursor: pointer; border-radius: 8px; border: 1px solid #999; background: transparent; }
      .preview { margin-top: 24px; display: grid; gap: 12px; align-items: start; grid-template-columns: 160px 1fr; }
      img { image-rendering: pixelated; border: 1px solid #ddd; width: 145px; height: 145px; border-radius: 6px; background: #fff; cursor: pointer; }
      .stats { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
      .muted { opacity: 0.7; }
      footer { margin-top: 28px; font-size: 14px; opacity: 0.75; text-align: center; }
      a { color: inherit; }
    </style>
  </head>
  <body>
    <header>
      <canvas id="logoCanvas" class="brand-logo" width="800" height="90" aria-label="MON5TERMATT"></canvas>
      <div class="tag">Built for <a href="https://wplace.live" target="_blank" rel="noopener">wplace.live</a> by <a href="https://mon5termatt.com" target="_blank" rel="noopener">MON5TERMATT</a> | Make QR codes to fit the smallest possible space, without fluff.</div>
    </header>

    

    <main>
    <form method="POST" onsubmit="return false">
      <label>
        Text to encode
        <input id="dataInput" type="text" name="data" value="{{ data or '' }}" placeholder="Enter text or URL" required />
      </label>
      <div class="controls">
        <div class="row">
          <label class="row" style="align-items:center;">
            Foreground
            <input id="dark" type="color" name="dark" value="{{ dark or '#000000' }}" />
          </label>
          <label class="row" style="align-items:center;">
            Background
            <input id="light" type="color" name="light" value="{{ light or '#FFFFFF' }}" />
          </label>
          <label class="row" style="align-items:center;">
            <input id="transparent" type="checkbox" name="transparent" value="1" {% if transparent %}checked{% endif %} /> Transparent background
          </label>
        </div>
        <div class="row">
          <label class="row" style="align-items:center;">
            Border
            <input id="border" type="range" name="border" min="0" max="50" step="1" value="{{ border or 0 }}" />
            <span class="muted"><span id="borderVal">{{ border or 0 }}</span> modules</span>
          </label>
          <label class="row" style="align-items:center;">
            Scale
            <input id="scale" type="range" name="scale" min="1" max="50" step="1" value="{{ scale or 1 }}" />
            <span class="muted"><span id="scaleVal">{{ scale or 1 }}</span> px/module</span>
          </label>
        </div>
      </div>
    </form>

    <div class="preview" id="preview" data-black="{{ black or 0 }}" data-version="{{ version or 3 }}" style="{{ '' if data else 'display:none' }}">
      <div>
        <img id="qrImg" src="{{ ('/download?data=' ~ (data|urlencode) ~ '&dark=' ~ (dark|urlencode) ~ '&light=' ~ (light|urlencode) ~ '&transparent=' ~ ((1 if transparent else 0)) ~ '&border=' ~ border ~ '&scale=' ~ scale) if data else 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==' }}" alt="QR preview" />
      </div>
      <div class="stats">
        <div><strong>Version</strong>: <span id="ver">{{ version or 3 }}</span> (<span id="sizeValPx">{{ size or 29 }}</span>x<span id="sizeValPx2">{{ size or 29 }}</span>)</div>
        <div><strong>Black</strong>: <span id="blackVal">{{ black or 0 }}</span></div>
        <div><strong>White</strong>: <span id="whiteVal">{{ white or 0 }}</span></div>
        <div><strong>Total</strong>: <span id="totalVal">{{ total or 841 }}</span></div>
        <div style="margin-top:8px">
          <a id="dlLink" href="{{ ('/download?data=' ~ (data|urlencode) ~ '&dark=' ~ (dark|urlencode) ~ '&light=' ~ (light|urlencode) ~ '&transparent=' ~ ((1 if transparent else 0)) ~ '&border=' ~ border ~ '&scale=' ~ scale) if data else '#' }}">Download PNG</a>
        </div>
        <div class="muted" style="margin-top:8px">Border: <span id="borderDisp">{{ border or 0 }}</span> · Scale: <span id="scaleDisp">{{ scale or 1 }}</span> px/module</div>
      </div>
    </div>
    </main>

    <main>
      <section class="bitmap-section">
        <h2 style="margin:0 0 8px 0;">Bitmap Text Generator</h2>
        <p class="muted" style="margin:0 0 12px 0;">Type text below to render as 5x7 pixel characters. Click the image to download.</p>
        <div class="controls">
          <label class="row" style="align-items:center;">
            Text
            <input type="text" id="bitmapInput" placeholder="Enter text to render as bitmap" style="flex:1; min-width:280px;" />
          </label>
          <div class="row" style="align-items:center;">
            <label class="row" style="align-items:center;">
              Scale
              <input id="bitmapScale" type="range" min="1" max="50" step="1" value="6" />
              <span class="muted"><span id="bitmapScaleVal">6</span> px/module</span>
            </label>
            <label class="row" style="align-items:center;">
              Border
              <input id="bitmapBorder" type="range" min="0" max="50" step="1" value="0" />
              <span class="muted"><span id="bitmapBorderVal">0</span> modules</span>
            </label>
            <a id="bitmapDownload" href="#" download="bitmap.png" style="margin-left:auto; text-decoration:none; border:1px solid #999; border-radius:8px; padding:8px 12px;">Download PNG</a>
          </div>
        </div>
        <div class="muted" style="margin-top:6px; font-size:12px;">Note: Very long text will auto-fit to your screen and may appear compressed.</div>
        <div id="bitmapContainer" style="margin-top:8px; width:100%;">
          <canvas id="bitmapCanvas" style="image-rendering: pixelated; border:1px solid #ddd; border-radius:6px; background:#fff; cursor:pointer; max-width:100%; height:auto; min-height:24px;"></canvas>
        </div>
      </section>
    </main>

    <footer>
      Minimal QR generator — No fluff! Size auto-steps up from 21x21 minimum only when needed. 
      <br>
      <br>Made by <a href="https://mon5termatt.com" target="_blank" rel="noopener">MON5TERMATT</a>
      <br>Source Code: <a href="https://github.com/mon5termatt/qr-wplace" target="_blank" rel="noopener">qr-wplace</a>
      <br>
      <br><script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script><script type='text/javascript'>kofiwidget2.init('Support me on Ko-fi', '#72a4f2', 'Y8Y37UTRU');kofiwidget2.draw();</script> 
    </footer>
  </body>
  <script>
    (function(){
      // 5x7 font for A-Z, 0-9 and dash; using '#' for on pixels per column-major rows
      const FONT_5x7 = {
        'A': [0b01110,0b10001,0b10001,0b11111,0b10001,0b10001,0b10001],
        'B': [0b11110,0b10001,0b10001,0b11110,0b10001,0b10001,0b11110],
        'C': [0b01110,0b10001,0b10000,0b10000,0b10000,0b10001,0b01110],
        'D': [0b11110,0b10001,0b10001,0b10001,0b10001,0b10001,0b11110],
        'E': [0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b11111],
        'F': [0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b10000],
        'G': [0b01110,0b10001,0b10000,0b10111,0b10001,0b10001,0b01110],
        'H': [0b10001,0b10001,0b10001,0b11111,0b10001,0b10001,0b10001],
        'I': [0b01110,0b00100,0b00100,0b00100,0b00100,0b00100,0b01110],
        'J': [0b00111,0b00010,0b00010,0b00010,0b10010,0b10010,0b01100],
        'K': [0b10001,0b10010,0b10100,0b11000,0b10100,0b10010,0b10001],
        'L': [0b10000,0b10000,0b10000,0b10000,0b10000,0b10000,0b11111],
        'M': [0b10001,0b11011,0b10101,0b10101,0b10001,0b10001,0b10001],
        'N': [0b10001,0b11001,0b10101,0b10011,0b10001,0b10001,0b10001],
        'O': [0b01110,0b10001,0b10001,0b10001,0b10001,0b10001,0b01110],
        'P': [0b11110,0b10001,0b10001,0b11110,0b10000,0b10000,0b10000],
        'Q': [0b01110,0b10001,0b10001,0b10001,0b10101,0b10010,0b01101],
        'R': [0b11110,0b10001,0b10001,0b11110,0b10100,0b10010,0b10001],
        'S': [0b01111,0b10000,0b10000,0b01110,0b00001,0b00001,0b11110],
        'T': [0b11111,0b00100,0b00100,0b00100,0b00100,0b00100,0b00100],
        'U': [0b10001,0b10001,0b10001,0b10001,0b10001,0b10001,0b01110],
        'V': [0b10001,0b10001,0b10001,0b10001,0b01010,0b01010,0b00100],
        'W': [0b10001,0b10001,0b10001,0b10101,0b10101,0b11011,0b10001],
        'X': [0b10001,0b01010,0b00100,0b00100,0b00100,0b01010,0b10001],
        'Y': [0b10001,0b01010,0b00100,0b00100,0b00100,0b00100,0b00100],
        'Z': [0b11111,0b00001,0b00010,0b00100,0b01000,0b10000,0b11111],
        '0': [0b01110,0b11011,0b10101,0b10101,0b10101,0b10011,0b01110],
        '1': [0b00100,0b01100,0b00100,0b00100,0b00100,0b00100,0b01110],
        '2': [0b01110,0b10001,0b00001,0b00010,0b00100,0b01000,0b11111],
        '3': [0b11110,0b00001,0b00001,0b01110,0b00001,0b00001,0b11110],
        '4': [0b00010,0b00110,0b01010,0b10010,0b11111,0b00010,0b00010],
        '5': [0b11111,0b10000,0b11110,0b00001,0b00001,0b10001,0b01110],
        '6': [0b00110,0b01000,0b10000,0b11110,0b10001,0b10001,0b01110],
        '7': [0b11111,0b00001,0b00010,0b00100,0b01000,0b01000,0b01000],
        '8': [0b01110,0b10001,0b10001,0b01110,0b10001,0b10001,0b01110],
        '9': [0b01110,0b10001,0b10001,0b01111,0b00001,0b00010,0b11100],
        '-': [0b00000,0b00000,0b00000,0b11111,0b00000,0b00000,0b00000],
        ' ': [0b00000,0b00000,0b00000,0b00000,0b00000,0b00000,0b00000],
        "'": [0b00100,0b00100,0b01000,0b00000,0b00000,0b00000,0b00000],
        '_': [0b00000,0b00000,0b00000,0b00000,0b00000,0b00000,0b11111],
        '+': [0b00100,0b00100,0b11111,0b00100,0b00100,0b00000,0b00000],
        '=': [0b00000,0b11111,0b00000,0b11111,0b00000,0b00000,0b00000],
        '[': [0b11110,0b10000,0b10000,0b10000,0b10000,0b10000,0b11110],
        ']': [0b01111,0b00001,0b00001,0b00001,0b00001,0b00001,0b01111],
        '{': [0b00110,0b00100,0b00100,0b11000,0b00100,0b00100,0b00110],
        '}': [0b01100,0b00100,0b00100,0b00011,0b00100,0b00100,0b01100],
        '|': [0b00100,0b00100,0b00100,0b00100,0b00100,0b00100,0b00100],
        '\\': [0b10000,0b01000,0b00100,0b00010,0b00001,0b00000,0b00000],
        '/': [0b00001,0b00010,0b00100,0b01000,0b10000,0b00000,0b00000],
        ':': [0b00000,0b00100,0b00000,0b00000,0b00000,0b00100,0b00000],
        ';': [0b00000,0b00100,0b00000,0b00000,0b00000,0b00100,0b01000],
        '"': [0b01010,0b01010,0b00000,0b00000,0b00000,0b00000,0b00000],
        '>': [0b10000,0b01000,0b00100,0b00010,0b00100,0b01000,0b10000],
        '<': [0b00001,0b00010,0b00100,0b01000,0b00100,0b00010,0b00001],
        '.': [0b00000,0b00000,0b00000,0b00000,0b00000,0b00100,0b00000],
        ',': [0b00000,0b00000,0b00000,0b00000,0b00000,0b00100,0b01000],
        '?': [0b01110,0b10001,0b00010,0b00100,0b00100,0b00000,0b00100]
      };

      function measureWordPx(word, px, spacing){
        const columnsPerChar = 5; const chars = String(word).toUpperCase().split('');
        return chars.length * (columnsPerChar*px) + Math.max(0, chars.length-1) * (spacing*px);
      }

      const GLYPH_CACHE = {};

      function synthesizeGlyph5x7(ch){
        // Render the character to an offscreen canvas and sample to 5x7 bitmap
        const off = document.createElement('canvas');
        const W = 56, H = 56; // generous draw area
        off.width = W; off.height = H;
        const octx = off.getContext('2d');
        octx.clearRect(0,0,W,H);
        octx.fillStyle = '#000';
        // Try to fit the glyph height to 7 rows with padding
        const targetRows = 7;
        // Start with a font size that fits vertically and adjust
        let fontSize = 40;
        octx.font = `${fontSize}px monospace`;
        octx.textBaseline = 'middle';
        octx.textAlign = 'center';
        // Draw center, then sample
        octx.fillText(ch, W/2, H/2);
        // Convert to 5x7 by sampling blocks
        const cols = 5; const rows = 7;
        const margin = 6; // around the glyph for safety
        const sampleWidth = W - margin*2;
        const sampleHeight = H - margin*2;
        const cellW = sampleWidth / cols;
        const cellH = sampleHeight / rows;
        const data = octx.getImageData(0,0,W,H).data;
        const bitmap = [];
        for (let r=0; r<rows; r++){
          let rowBits = 0;
          for (let c=0; c<cols; c++){
            // Sample a point near the center of the cell
            const sx = Math.floor(margin + c*cellW + cellW/2);
            const sy = Math.floor(margin + r*cellH + cellH/2);
            const idx = (sy*W + sx) * 4;
            const alpha = data[idx+3];
            const on = alpha > 32 ? 1 : 0;
            rowBits = (rowBits << 1) | on;
          }
          bitmap.push(rowBits);
        }
        return bitmap;
      }

      function getGlyph5x7(ch){
        const up = String(ch).toUpperCase();
        if (FONT_5x7[up]) return FONT_5x7[up];
        if (GLYPH_CACHE[up]) return GLYPH_CACHE[up];
        const bm = synthesizeGlyph5x7(up);
        GLYPH_CACHE[up] = bm;
        return bm;
      }

      function drawWordAt(ctx, word, colorOrFn, xStart, yStart, px, totalWidth){
        const columnsPerChar = 5; const rows = 7; const spacing = 2; const chars = String(word).toUpperCase().split('');
        const isFn = typeof colorOrFn === 'function';
        let x = xStart;
        for (const ch of chars){
          const glyphRows = getGlyph5x7(ch);
          for (let row=0; row<rows; row++){
            const bits = glyphRows[row] || 0;
            for (let col=0; col<columnsPerChar; col++){
              const on = (bits >> (columnsPerChar-1-col)) & 1;
              if (on){
                const xPos = x + col*px;
                const t = totalWidth > 0 ? Math.min(1, Math.max(0, (xPos) / totalWidth)) : 0;
                ctx.fillStyle = isFn ? colorOrFn(t) : colorOrFn;
                ctx.fillRect(xPos, yStart + row*px, px, px);
              }
            }
          }
          x += columnsPerChar*px + spacing*px;
        }
      }

      function hslToRgb(h, s, l){
        h = (h % 360 + 360) % 360; s = Math.max(0, Math.min(1, s)); l = Math.max(0, Math.min(1, l));
        const c = (1 - Math.abs(2*l - 1)) * s;
        const x = c * (1 - Math.abs((h/60) % 2 - 1));
        const m = l - c/2;
        let r=0,g=0,b=0;
        if (0<=h && h<60){ r=c; g=x; b=0; }
        else if (60<=h && h<120){ r=x; g=c; b=0; }
        else if (120<=h && h<180){ r=0; g=c; b=x; }
        else if (180<=h && h<240){ r=0; g=x; b=c; }
        else if (240<=h && h<300){ r=x; g=0; b=c; }
        else { r=c; g=0; b=x; }
        return [Math.round((r+m)*255), Math.round((g+m)*255), Math.round((b+m)*255)];
      }

      function drawLogo(canvas, topText, bottomText, color, hueOffset){
        const ctx = canvas.getContext('2d');
        const padding = 6; const spacingCols = 2; const lineGapPx = 8; // space between lines
        let px = 6; // pixel block size
        const columnsPerChar = 5; const rows = 7;
        const wTop = measureWordPx(topText, px, spacingCols);
        const wBot = measureWordPx(bottomText, px, spacingCols);
        const widthPx = padding*2 + Math.max(wTop, wBot);
        const heightPx = padding*2 + rows*px*2 + lineGapPx;
        canvas.width = widthPx; canvas.height = heightPx;
        ctx.clearRect(0,0,canvas.width,canvas.height);
        // Center each line horizontally
        const topX = padding + Math.floor((Math.max(wTop,wBot) - wTop)/2);
        const botX = padding + Math.floor((Math.max(wTop,wBot) - wBot)/2);
        const topY = padding;
        const botY = padding + rows*px + lineGapPx;
        const colorSupplier = (color === 'rainbow')
          ? (t) => { const [r,g,b] = hslToRgb((t*360 + (hueOffset||0)), 1, 0.6); return `rgb(${r},${g},${b})`; }
          : color;
        drawWordAt(ctx, topText, colorSupplier, topX, topY, px, widthPx);
        drawWordAt(ctx, bottomText, colorSupplier, botX, botY, px, widthPx);
      }

      const logo = document.getElementById('logoCanvas');
      const darkInput = document.getElementById('dark');
      if (logo){
        let hue = 0;
        function animate(ts){
          hue = (hue + 0.6) % 360; // speed: degrees per frame
          drawLogo(logo, 'QR Code Generator for wplace', 'by MON5TERMATT', 'rainbow', hue);
          requestAnimationFrame(animate);
        }
        requestAnimationFrame(animate);
      }
      const img = document.getElementById('qrImg');
      const preview = document.getElementById('preview');
      const border = document.getElementById('border');
      const scale = document.getElementById('scale');
      const dataInput = document.getElementById('dataInput');
      const dark = document.getElementById('dark');
      const light = document.getElementById('light');
      const transparent = document.getElementById('transparent');
      if (!img || !preview || !border || !scale) return;
      let black = parseInt(preview.dataset.black || '0', 10);
      let version = parseInt(preview.dataset.version || '3', 10);
      function modulesFor(ver){ return 17 + 4 * ver; }
      const borderVal = document.getElementById('borderVal');
      const scaleVal = document.getElementById('scaleVal');
      const sizeValPx = document.getElementById('sizeValPx');
      const sizeValPx2 = document.getElementById('sizeValPx2');
      const whiteEl = document.getElementById('whiteVal');
      const totalEl = document.getElementById('totalVal');
      const borderDisp = document.getElementById('borderDisp');
      const scaleDisp = document.getElementById('scaleDisp');
      const dl = document.getElementById('dlLink');
      const bitmapCanvas = document.getElementById('bitmapCanvas');
      const bitmapInput = document.getElementById('bitmapInput');
      const bitmapScale = document.getElementById('bitmapScale');
      const bitmapScaleVal = document.getElementById('bitmapScaleVal');
      const bitmapBorder = document.getElementById('bitmapBorder');
      const bitmapBorderVal = document.getElementById('bitmapBorderVal');
      const bitmapDownload = document.getElementById('bitmapDownload');

      function buildUrl() {
        const params = new URLSearchParams(window.location.search);
        // Pull form values directly
        const darkVal = (dark ? dark.value : '#000000');
        const lightVal = (light ? light.value : '#FFFFFF');
        const transparentVal = (transparent && transparent.checked ? '1' : '0');
        const dataField = (dataInput ? dataInput.value : '');
        params.set('data', dataField);
        params.set('dark', darkVal);
        params.set('light', lightVal);
        params.set('transparent', transparentVal);
        params.set('border', String(border.value));
        params.set('scale', String(scale.value));
        params.set('t', String(Date.now())); // cache bust
        return '/download?' + params.toString();
      }

      function recompute(modules) {
        const b = parseInt(border.value, 10);
        const s = parseInt(scale.value, 10);
        const size = (modules + 2*b) * s;
        const total = size * size;
        const white = total - black;
        if (borderVal) borderVal.textContent = String(b);
        if (scaleVal) scaleVal.textContent = String(s);
        if (sizeValPx) sizeValPx.textContent = String(size);
        if (sizeValPx2) sizeValPx2.textContent = String(size);
        if (whiteEl) whiteEl.textContent = String(white);
        if (totalEl) totalEl.textContent = String(total);
        if (borderDisp) borderDisp.textContent = String(b);
        if (scaleDisp) scaleDisp.textContent = String(s);
      }

      function update() {
        // Use latest version for module count
        const modules = modulesFor(version);
        recompute(modules);
        const url = buildUrl();
        // Show preview when there is data, hide when empty
        const hasData = (dataInput && dataInput.value && dataInput.value.trim().length > 0);
        const container = document.getElementById('preview');
        if (container) container.style.display = hasData ? '' : 'none';
        if (hasData) img.src = url; else img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';
        if (dl) dl.href = url.replace(/&t=\d+/, '');
      }

      // Debounce helper
      function debounce(fn, ms){ let t; return function(){ clearTimeout(t); t = setTimeout(fn, ms); }; }

      async function refreshMeta(){
        const params = new URLSearchParams(window.location.search);
        const darkVal = (dark ? dark.value : '#000000');
        const lightVal = (light ? light.value : '#FFFFFF');
        const transparentVal = (transparent && transparent.checked ? '1' : '0');
        const dataField = (dataInput ? dataInput.value : '');
        params.set('data', dataField);
        params.set('dark', darkVal);
        params.set('light', lightVal);
        params.set('transparent', transparentVal);
        params.set('border', String(border.value));
        params.set('scale', String(scale.value));
        try {
          const res = await fetch('/meta?' + params.toString(), { cache: 'no-store' });
          if (!res.ok) return;
          const meta = await res.json();
          if (typeof meta.version === 'number') {
            version = meta.version;
            black = meta.black;
            const modules = modulesFor(version);
            recompute(modules);
            const verEl = document.getElementById('ver');
            if (verEl) verEl.textContent = String(meta.version);
            const blackEl = document.getElementById('blackVal');
            if (blackEl) blackEl.textContent = String(meta.black);
          }
        } catch (_) { /* ignore */ }
      }

      const liveUpdate = debounce(function(){ update(); refreshMeta(); }, 120);

      border.addEventListener('input', liveUpdate);
      scale.addEventListener('input', liveUpdate);
      if (dataInput) dataInput.addEventListener('input', liveUpdate);
      if (dark) dark.addEventListener('input', liveUpdate);
      if (light) light.addEventListener('input', liveUpdate);
      if (transparent) transparent.addEventListener('change', liveUpdate);

      // Click QR image to trigger download
      if (img) img.addEventListener('click', function(e){
        e.preventDefault();
        if (dl) {
          // Force latest URL, then simulate click
          update();
          dl.click();
        }
      });

      // Bitmap Text Generator
      function drawBitmap(canvas, text, px, color, borderModules){
        const ctx = canvas.getContext('2d');
        const spacingCols = 2; const columnsPerChar = 5; const rows = 7;
        const padding = Math.max(0, borderModules|0) * px;
        const chars = String(text || '').toUpperCase().split('');
        if (chars.length === 0){ canvas.width = 0; canvas.height = 0; return; }
        const widthPx = padding*2 + chars.length * (columnsPerChar*px) + (Math.max(0, chars.length-1)) * (spacingCols*px);
        const heightPx = padding*2 + rows*px;
        canvas.width = widthPx; canvas.height = heightPx;
        ctx.clearRect(0,0,widthPx,heightPx);
        let x = padding;
        for (const ch of chars){
          const glyph = getGlyph5x7(ch);
          for (let r=0;r<rows;r++){
            const bits = glyph[r] || 0;
            for (let c=0;c<columnsPerChar;c++){
              const on = (bits >> (columnsPerChar-1-c)) & 1;
              if (on){ ctx.fillStyle = color; ctx.fillRect(x + c*px, padding + r*px, px, px); }
            }
          }
          x += columnsPerChar*px + spacingCols*px;
        }
      }

      function updateBitmap(){
        const txt = bitmapInput ? bitmapInput.value : '';
        const px = bitmapScale ? parseInt(bitmapScale.value, 10) : 6;
        const b = bitmapBorder ? parseInt(bitmapBorder.value, 10) : 0;
        if (bitmapScaleVal) bitmapScaleVal.textContent = String(px);
        if (bitmapBorderVal) bitmapBorderVal.textContent = String(b);
        // Compute max px to fit container width
        const container = document.getElementById('bitmapContainer');
        let fitPx = px;
        if (container){
          const columnsPerChar = 5; const spacingCols = 2; const rows = 7;
          const chars = String(txt || '').toUpperCase().split('');
          const padding = Math.max(0, b|0);
          const containerWidth = container.clientWidth || container.offsetWidth || 0;
          if (chars.length > 0 && containerWidth > 0){
            const modulesWide = (padding*2) + (chars.length * columnsPerChar) + (Math.max(0, chars.length-1) * spacingCols);
            const maxPx = Math.max(1, Math.floor(containerWidth / modulesWide));
            fitPx = Math.min(px, maxPx);
          }
        }
        drawBitmap(bitmapCanvas, txt, fitPx, '#000', b);
        // Update download link
        if (bitmapDownload){
          const dataUrl = bitmapCanvas.toDataURL('image/png');
          bitmapDownload.href = dataUrl;
          const slug = (txt || 'bitmap').replace(/[^A-Za-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,50) || 'bitmap';
          bitmapDownload.download = slug + '.png';
        }
      }

      if (bitmapInput){
        bitmapInput.addEventListener('input', updateBitmap);
      }
      if (bitmapScale){
        bitmapScale.addEventListener('input', updateBitmap);
      }
      if (bitmapBorder){
        bitmapBorder.addEventListener('input', updateBitmap);
      }
      if (bitmapCanvas){
        bitmapCanvas.addEventListener('click', function(){ if (bitmapDownload) bitmapDownload.click(); });
      }
      // initial
      updateBitmap();
      window.addEventListener('resize', updateBitmap);
    })();
  </script>
  </html>
"""


def _normalize_hex(color: str) -> str:
    c = color.strip()
    if c.startswith('#') and (len(c) == 7 or len(c) == 4):
        return c
    return c


def try_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except Exception:
        return False


def generate_qr_bytes(
    data: str,
    *,
    dark_color: str = "#000000",
    light_color: str = "#FFFFFF",
    transparent: bool = False,
    border: int = 0,
    scale: int = 1,
) -> Tuple[bytes, int, int, int, int]:
    dark_color = _normalize_hex(dark_color)
    light_color = _normalize_hex(light_color)
    if border < 0:
        border = 0
    if scale < 1:
        scale = 1

    segno_available = try_import('segno')
    qrcode_available = try_import('qrcode')
    if not (segno_available or qrcode_available):
        raise SystemExit(
            "No QR libraries found. Install one of:\n"
            "  pip install segno\n"
            "  or\n"
            "  pip install qrcode[pil]"
        )

    # Enforce minimum standard QR version = 1 (21x21). No Micro QR.
    if segno_available:
        import segno  # type: ignore
        last_error: Optional[Exception] = None
        for version in range(1, 41):
            try:
                qr = segno.make(
                    data,
                    version=version,
                    error='l',
                    micro=False,
                    boost_error=False,
                )
                try:
                    matrix = qr.matrix  # type: ignore[attr-defined]
                except Exception:
                    matrix = [list(row) for row in qr.matrix_iter(scale=1, border=0)]  # type: ignore[attr-defined]
                black = sum(1 for row in matrix for v in row if v)
                modules_per_side = len(matrix[0]) if matrix else (17 + 4 * version)
                size = (modules_per_side + 2 * border) * scale
                total = size * size
                white = total - black
                buf = io.BytesIO()
                segno_light = None if transparent else light_color
                qr.save(buf, kind='png', scale=scale, border=border, dark=dark_color, light=segno_light)
                return buf.getvalue(), black, white, version, size
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error

    # Fallback to qrcode: let it choose minimal standard version
    if qrcode_available:
        import qrcode  # type: ignore
        from qrcode.constants import ERROR_CORRECT_L  # type: ignore
        # Increment from version 1 upward until it fits
        version = 1
        qr = qrcode.QRCode(
            version=version,
            error_correction=ERROR_CORRECT_L,
            box_size=scale,
            border=border,
        )
        qr.add_data(data)
        try:
            qr.make(fit=False)
        except Exception:
            # try higher versions
            for version in range(2, 41):
                qr = qrcode.QRCode(
                    version=version,
                    error_correction=ERROR_CORRECT_L,
                    box_size=scale,
                    border=border,
                )
                qr.add_data(data)
                try:
                    qr.make(fit=False)
                    break
                except Exception:
                    continue
        fill = dark_color
        back = (255, 255, 255, 0) if transparent else light_color
        img = qr.make_image(fill_color=fill, back_color=back)
        img = img.convert('RGBA' if transparent else 'RGB')
        width, height = img.size
        matrix = qr.get_matrix()
        black = sum(1 for row in matrix for v in row if v)
        modules_per_side = len(matrix[0]) if matrix else (17 + 4 * version)
        size = (modules_per_side + 2 * border) * scale
        total = size * size
        white = total - black
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        version = (modules_per_side - 17) // 4 if modules_per_side >= 21 else 1
        return buf.getvalue(), black, white, version, size

    raise RuntimeError("No QR libraries available.")


def filename_for_data(data: str, ext: str = 'png') -> str:
    # Create a readable slug plus a short hash for uniqueness
    slug = re.sub(r"[^A-Za-z0-9]+", "-", data.strip()).strip("-")
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')
    if not slug:
        slug = "qr"
    digest = hashlib.sha256(data.encode('utf-8')).hexdigest()[:10]
    return f"{slug}-{digest}.{ext}"


@app.route('/', methods=['GET', 'POST'])
def index():
    data = request.form.get('data') if request.method == 'POST' else request.args.get('data')
    dark = (request.form.get('dark') if request.method == 'POST' else request.args.get('dark')) or '#000000'
    light = (request.form.get('light') if request.method == 'POST' else request.args.get('light')) or '#FFFFFF'
    transparent = (request.form.get('transparent') == '1') if request.method == 'POST' else (request.args.get('transparent') == '1')
    try:
        border = int(request.form.get('border') if request.method == 'POST' else (request.args.get('border') or 0))
    except Exception:
        border = 0
    try:
        scale = int(request.form.get('scale') if request.method == 'POST' else (request.args.get('scale') or 1))
    except Exception:
        scale = 1
    png_b64 = None
    context = dict(data=data or '', dark=dark, light=light, transparent=transparent, border=border, scale=scale)
    if data:
        png_bytes, black, white, version, size = generate_qr_bytes(
            data,
            dark_color=dark,
            light_color=light,
            transparent=transparent,
            border=border,
            scale=scale,
        )
        import base64
        png_b64 = base64.b64encode(png_bytes).decode('ascii')
        context.update(dict(png_data=png_b64, black=black, white=white, total=size * size, version=version, size=size))
    return render_template_string(PAGE, **context)


@app.route('/download')
def download():
    data = request.args.get('data') or ''
    dark = request.args.get('dark') or '#000000'
    light = request.args.get('light') or '#FFFFFF'
    transparent = (request.args.get('transparent') == '1')
    try:
        border = int(request.args.get('border') or 0)
    except Exception:
        border = 0
    try:
        scale = int(request.args.get('scale') or 1)
    except Exception:
        scale = 1
    if not data:
        return "Missing data", 400
    png_bytes, black, white, version, size = generate_qr_bytes(
        data,
        dark_color=dark,
        light_color=light,
        transparent=transparent,
        border=border,
        scale=scale,
    )
    fname = filename_for_data(data, 'png')
    return send_file(io.BytesIO(png_bytes), mimetype='image/png', as_attachment=True, download_name=fname)


@app.route('/meta')
def meta():
    data = request.args.get('data') or ''
    if not data:
        return jsonify({"error": "Missing data"}), 400
    dark = request.args.get('dark') or '#000000'
    light = request.args.get('light') or '#FFFFFF'
    transparent = (request.args.get('transparent') == '1')
    try:
        border = int(request.args.get('border') or 0)
    except Exception:
        border = 0
    try:
        scale = int(request.args.get('scale') or 1)
    except Exception:
        scale = 1
    png_bytes, black, white, version, size = generate_qr_bytes(
        data,
        dark_color=dark,
        light_color=light,
        transparent=transparent,
        border=border,
        scale=scale,
    )
    return jsonify(dict(version=version, black=black, white=white, total=size * size, size=size))


@app.get('/favicon.svg')
def favicon_svg() -> Response:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
        "<rect width='64' height='64' rx='8' fill='#000'/>"
        "<rect x='10' y='10' width='44' height='44' fill='#fff'/>"
        "<rect x='14' y='14' width='12' height='12' fill='#000'/>"
        "<rect x='38' y='14' width='12' height='12' fill='#000'/>"
        "<rect x='14' y='38' width='12' height='12' fill='#000'/>"
        "<rect x='28' y='28' width='8' height='8' fill='#000'/>"
        "</svg>"
    )
    return Response(svg, mimetype='image/svg+xml')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


