// src/components/PoseOverlay.jsx
import React, { useRef, useEffect } from 'react';
import { getPostureLabel, getViewpointLabel, get3StatePosture } from '../utils/postureLabels';

/**
 * Circle Severity Mapping derived strictly from backend risk_level / temporal_state:
 * - NORMAL: Light Yellow (#FACC15, RGB 250, 204, 21), Small Radius (24px)
 * - WATCH: Vibrant Orange (#F97316, RGB 249, 115, 22), Medium Radius (34px, ~1.4x)
 * - ACTIVE_RISK / ALERT: Glowing Red (#EF4444, RGB 239, 68, 68), Large Radius (46px, ~1.9x)
 * - RECOVERING: Sky Blue (#38BDF8, RGB 56, 189, 248), Medium-Small Radius (30px)
 * - COOLDOWN: Neutral Zinc (#A1A1AA, RGB 161, 161, 170), Small Radius (24px)
 */
function getRiskConfig(riskLevel, temporalState) {
  const state = (temporalState || riskLevel || 'NORMAL').toUpperCase();

  switch (state) {
    case 'WATCH':
      return { state, radius: 34, r: 249, g: 115, b: 22, hex: '#F97316' };
    case 'ACTIVE_RISK':
    case 'ALERT':
      return { state, radius: 46, r: 239, g: 68, b: 68, hex: '#EF4444' };
    case 'RECOVERING':
      return { state, radius: 30, r: 56, g: 189, b: 248, hex: '#38BDF8' };
    case 'COOLDOWN':
      return { state, radius: 24, r: 161, g: 161, b: 170, hex: '#A1A1AA' };
    case 'NORMAL':
    default:
      return { state, radius: 24, r: 250, g: 204, b: 21, hex: '#FACC15' };
  }
}

// Map posture code to human lean orientation for CV HUD
function getLeanDirection(postureCode) {
  switch (postureCode) {
    case 'TUP': return 'CENTERED';
    case 'TLF': return 'TRUNK PITCH TILT';
    case 'TLB': return 'TRUNK BACKWARD TILT';
    case 'TLL': return 'LEFT LEAN';
    case 'TLR': return 'RIGHT LEAN';
    default: return 'CENTERED';
  }
}

export default function PoseOverlay({
  poseLandmarks,
  posture,
  confidence,
  viewpoint,
  riskScore,
  riskLevel,
  temporalState,
  trackingState,
  candidates = [],
  onSelectCandidate,
  videoAspect = 4 / 3,
  isMirrored = false,
  debugMode = false,
}) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const smoothedPtsRef = useRef([]);

  // Smooth dynamic circle radius & color state references
  const animCircleRef = useRef({ radius: 24, r: 250, g: 204, b: 21 });

  const handleCanvasClick = (e) => {
    if (!onSelectCandidate || !candidates || candidates.length === 0) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = (e.clientX - rect.left) / rect.width;
    const clickY = (e.clientY - rect.top) / rect.height;

    for (const cand of candidates) {
      const bbox = cand.bbox;
      if (
        clickX >= bbox.x &&
        clickX <= bbox.x + bbox.width &&
        clickY >= bbox.y &&
        clickY <= bbox.y + bbox.height
      ) {
        onSelectCandidate(cand.temp_id);
        break;
      }
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const render = () => {
      // 1. Sync canvas size to container bounding box
      const rect = canvas.getBoundingClientRect();
      if (canvas.width !== rect.width || canvas.height !== rect.height) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }

      const containerW = canvas.width;
      const containerH = canvas.height;

      ctx.clearRect(0, 0, containerW, containerH);

      if (containerW === 0 || containerH === 0) {
        animFrameRef.current = requestAnimationFrame(render);
        return;
      }

      // 2. Calculate object-contain render bounds & letterbox offsets
      const containerAspect = containerW / containerH;
      let renderW, renderH, offsetX, offsetY;

      if (containerAspect > videoAspect) {
        renderH = containerH;
        renderW = containerH * videoAspect;
        offsetX = (containerW - renderW) / 2;
        offsetY = 0;
      } else {
        renderW = containerW;
        renderH = containerW / videoAspect;
        offsetX = 0;
        offsetY = (containerH - renderH) / 2;
      }

      // --- 3. DRAW CANDIDATE BOUNDING BOXES ---
      const isTargetSelected = trackingState === 'TARGET_TRACKING' || (candidates && candidates.some(c => c.is_target));
      const showAllCandidates = !isTargetSelected || debugMode;

      if (candidates && candidates.length > 0) {
        candidates.forEach((cand) => {
          if (!cand.bbox) return;
          const isTarget = cand.is_target;
          if (!showAllCandidates && !isTarget) return;

          const normX = isMirrored ? 1.0 - (cand.bbox.x + cand.bbox.width) : cand.bbox.x;
          const boxX = offsetX + normX * renderW;
          const boxY = offsetY + cand.bbox.y * renderH;
          const boxW = cand.bbox.width * renderW;
          const boxH = cand.bbox.height * renderH;

          ctx.save();
          if (isTarget) {
            ctx.strokeStyle = '#06B6D4'; // Highlight Cyan
            ctx.lineWidth = 3;
            ctx.setLineDash([]);
            ctx.strokeRect(boxX, boxY, boxW, boxH);

            ctx.fillStyle = 'rgba(6, 182, 212, 0.9)';
            ctx.fillRect(boxX, Math.max(0, boxY - 24), Math.max(130, boxW * 0.5), 24);
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 12px sans-serif';
            ctx.fillText(`Monitoring #${cand.temp_id}`, boxX + 6, Math.max(16, boxY - 7));
          } else {
            ctx.strokeStyle = 'rgba(245, 158, 11, 0.9)'; // Amber prompt box
            ctx.lineWidth = 2.5;
            ctx.setLineDash([6, 4]);
            ctx.strokeRect(boxX, boxY, boxW, boxH);

            ctx.fillStyle = 'rgba(245, 158, 11, 0.95)';
            ctx.fillRect(boxX, Math.max(0, boxY - 24), 140, 24);
            ctx.fillStyle = '#0F172A';
            ctx.font = 'bold 12px sans-serif';
            ctx.fillText(`Click to Select #${cand.temp_id}`, boxX + 6, Math.max(16, boxY - 7));
          }
          ctx.restore();
        });

        // Top prompt banner when multiple people are detected and awaiting selection
        if (!isTargetSelected && candidates.length > 1) {
          ctx.save();
          ctx.font = 'bold 14px sans-serif';
          const promptText = 'Multiple people detected — click a box to select the person to monitor.';
          const tw = ctx.measureText(promptText).width;
          const px = offsetX + (renderW - tw) / 2 - 16;
          const py = offsetY + 16;
          ctx.fillStyle = 'rgba(15, 23, 42, 0.90)';
          ctx.fillRect(px, py, tw + 32, 34);
          ctx.strokeStyle = '#F59E0B';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(px, py, tw + 32, 34);
          ctx.fillStyle = '#F59E0B';
          ctx.fillText(promptText, px + 16, py + 22);
          ctx.restore();
        }
      }

      const hasPose = isTargetSelected && poseLandmarks && Array.isArray(poseLandmarks) && poseLandmarks.length >= 33;
      const targetRiskCfg = getRiskConfig(riskLevel, temporalState);

      // Interpolate dynamic circle size & RGB color smoothly (15% step per frame)
      const currentCircle = animCircleRef.current;
      currentCircle.radius += (targetRiskCfg.radius - currentCircle.radius) * 0.15;
      currentCircle.r += (targetRiskCfg.r - currentCircle.r) * 0.15;
      currentCircle.g += (targetRiskCfg.g - currentCircle.g) * 0.15;
      currentCircle.b += (targetRiskCfg.b - currentCircle.b) * 0.15;

      const currR = Math.round(currentCircle.r);
      const currG = Math.round(currentCircle.g);
      const currB = Math.round(currentCircle.b);
      const activeFillRGBA = (alpha) => `rgba(${currR}, ${currG}, ${currB}, ${alpha})`;

      if (hasPose) {
        // 4. Target Points calculation with lerp smoothing for 60 FPS motion
        const targetPts = poseLandmarks.map((lm) => {
          if (!lm) return null;
          const normX = isMirrored ? (1.0 - lm.x) : lm.x;
          return {
            x: offsetX + normX * renderW,
            y: offsetY + lm.y * renderH,
          };
        });

        if (smoothedPtsRef.current.length !== targetPts.length) {
          smoothedPtsRef.current = targetPts.map(p => p ? { ...p } : null);
        } else {
          // Smooth lerp (35% step) towards new target coordinates
          for (let i = 0; i < targetPts.length; i++) {
            const target = targetPts[i];
            const curr = smoothedPtsRef.current[i];
            if (target && curr) {
              curr.x += (target.x - curr.x) * 0.35;
              curr.y += (target.y - curr.y) * 0.35;
            } else {
              smoothedPtsRef.current[i] = target ? { ...target } : null;
            }
          }
        }

        const getPt = (idx) => smoothedPtsRef.current[idx] || null;

        const drawLine = (p1, p2, color, width = 3.5, dash = []) => {
          if (!p1 || !p2) return;
          ctx.beginPath();
          ctx.setLineDash(dash);
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = color;
          ctx.lineWidth = width;
          ctx.lineCap = 'round';
          ctx.stroke();
          ctx.setLineDash([]);
        };

        const drawCircle = (p, radius, fillFn) => {
          if (!p) return;
          const grad = ctx.createRadialGradient(p.x, p.y, radius * 0.1, p.x, p.y, radius);
          grad.addColorStop(0, fillFn(0.85));
          grad.addColorStop(0.7, fillFn(0.5));
          grad.addColorStop(1, fillFn(0.1));

          ctx.beginPath();
          ctx.arc(p.x, p.y, radius, 0, 2 * Math.PI);
          ctx.fillStyle = grad;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(p.x, p.y, radius, 0, 2 * Math.PI);
          ctx.strokeStyle = fillFn(0.9);
          ctx.lineWidth = 2;
          ctx.stroke();
        };

        const drawDot = (p, radius, color) => {
          if (!p) return;
          ctx.beginPath();
          ctx.arc(p.x, p.y, radius, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        };

        // Key landmarks
        const nose = getPt(0);
        const leftEye = getPt(2);
        const rightEye = getPt(5);
        const leftShoulder = getPt(11);
        const rightShoulder = getPt(12);
        const leftElbow = getPt(13);
        const rightElbow = getPt(14);
        const leftWrist = getPt(15);
        const rightWrist = getPt(16);
        const leftHip = getPt(23);
        const rightHip = getPt(24);

        // Midpoints
        const midShoulder = (leftShoulder && rightShoulder) ? {
          x: (leftShoulder.x + rightShoulder.x) / 2,
          y: (leftShoulder.y + rightShoulder.y) / 2,
        } : null;

        // Derived Neck / Base-of-Head point
        const neckBase = (nose && midShoulder) ? {
          x: nose.x * 0.35 + midShoulder.x * 0.65,
          y: nose.y * 0.35 + midShoulder.y * 0.65,
        } : (midShoulder || nose);

        const midHip = (leftHip && rightHip) ? {
          x: (leftHip.x + rightHip.x) / 2,
          y: (leftHip.y + rightHip.y) / 2,
        } : null;

        const midSpine = (midShoulder && midHip) ? {
          x: (midShoulder.x + midHip.x) / 2,
          y: (midShoulder.y + midHip.y) / 2,
        } : null;

        // --- DRAW SKELETON & DYNAMIC CIRCLE GRAPHICS OVERLAY ---

        // 1. Dynamic Circle Target Rings
        if (neckBase) drawCircle(neckBase, currentCircle.radius, activeFillRGBA);
        if (leftShoulder) drawCircle(leftShoulder, currentCircle.radius * 0.8, (a) => `rgba(234, 179, 8, ${a})`);
        if (rightShoulder) drawCircle(rightShoulder, currentCircle.radius * 0.8, (a) => `rgba(234, 179, 8, ${a})`);
        if (midSpine) drawCircle(midSpine, currentCircle.radius * 0.7, activeFillRGBA);

        // 2. Plumb Lines
        if (midShoulder) {
          const spineBottomY = midHip ? midHip.y + 40 : midShoulder.y + 160;
          drawLine(midShoulder, { x: midShoulder.x, y: spineBottomY }, '#06B6D4', 2.5);
        }

        // 3. Head-to-Neck Axis Line
        if (nose && neckBase) drawLine(nose, neckBase, '#FACC15', 4);
        if (neckBase && midShoulder) drawLine(neckBase, midShoulder, '#FACC15', 4);

        // 4. Cyan Spine Line
        if (midShoulder && midHip) drawLine(midShoulder, midHip, '#06B6D4', 4.5);

        // 5. Bounding Magenta Skeleton Lines
        const magenta = '#E056FD';
        if (leftEye && rightEye) drawLine(leftEye, rightEye, magenta, 2.5);
        if (nose && leftEye) drawLine(nose, leftEye, magenta, 2);
        if (nose && rightEye) drawLine(nose, rightEye, magenta, 2);

        if (leftShoulder && rightShoulder) drawLine(leftShoulder, rightShoulder, magenta, 3.5);
        drawLine(leftShoulder, leftElbow, magenta, 3);
        drawLine(leftElbow, leftWrist, magenta, 3);
        drawLine(rightShoulder, rightElbow, magenta, 3);
        drawLine(rightElbow, rightWrist, magenta, 3);

        drawLine(leftShoulder, leftHip, magenta, 3);
        drawLine(rightShoulder, rightHip, magenta, 3);
        drawLine(leftHip, rightHip, magenta, 3);

        // 6. Joint Dots
        drawDot(nose, 6, '#FACC15');
        drawDot(neckBase, 7, targetRiskCfg.hex);
        drawDot(midShoulder, 6.5, '#06B6D4');
        drawDot(leftShoulder, 5.5, '#EAB308');
        drawDot(rightShoulder, 5.5, '#EAB308');
        drawDot(leftElbow, 4.5, '#E056FD');
        drawDot(rightElbow, 4.5, '#E056FD');
        drawDot(leftWrist, 4.5, '#E056FD');
        drawDot(rightWrist, 4.5, '#E056FD');
        drawDot(midHip, 6, '#06B6D4');
      } else {
        smoothedPtsRef.current = [];
      }

      // --- IN-FEED DIAGNOSTIC HUD OVERLAY ---
      if (posture || viewpoint || riskLevel || trackingState) {
        const hudX = offsetX + 18;
        const hudY = offsetY + 28;
        const lineH = 22;
        let curY = hudY;

        ctx.font = 'bold 14px "JetBrains Mono", "Courier New", monospace';

        const drawHudLine = (label, value, valueColor = '#00FF00') => {
          const fullText = `${label}: ${value}`;
          ctx.fillStyle = '#000000';
          ctx.fillText(fullText, hudX + 1.5, curY + 1.5);
          ctx.fillText(fullText, hudX - 1, curY - 1);
          
          ctx.fillStyle = valueColor;
          ctx.fillText(fullText, hudX, curY);
          curY += lineH;
        };

        const viewStr = getViewpointLabel(viewpoint).toUpperCase();
        drawHudLine('View', viewStr, '#22C55E');

        const leanStr = getLeanDirection(posture);
        drawHudLine('Lean', leanStr, posture === 'TUP' ? '#22C55E' : '#F97316');

        if (posture) {
          const threeState = get3StatePosture(posture, riskLevel, temporalState);
          const postureText = `${threeState.status} (${getPostureLabel(posture).toUpperCase()})`;
          drawHudLine('Posture', postureText, threeState.accentColor);
        }

        const activeStateLabel = targetRiskCfg.state;
        drawHudLine('Severity', activeStateLabel, targetRiskCfg.hex);

        if (confidence != null) {
          drawHudLine('Confidence', `${(confidence * 100).toFixed(0)}%`, '#22C55E');
        }

        drawHudLine('Risk', activeStateLabel, targetRiskCfg.hex);
      }

      // --- BOTTOM-LEFT POSTURE CORRECTION ALERT BANNER ---
      if (targetRiskCfg.state === 'ACTIVE_RISK' || targetRiskCfg.state === 'ALERT') {
        const alertY = offsetY + renderH - 24;
        const alertX = offsetX + 18;

        ctx.font = 'bold 18px "Plus Jakarta Sans", "Arial Black", sans-serif';
        const alertText = 'Correct your posture!';

        const textWidth = ctx.measureText(alertText).width;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
        ctx.fillRect(alertX - 6, alertY - 20, textWidth + 16, 28);

        ctx.fillStyle = '#EF4444';
        ctx.fillText(alertText, alertX, alertY);
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [poseLandmarks, posture, confidence, viewpoint, riskScore, riskLevel, temporalState, trackingState, candidates, videoAspect, isMirrored, debugMode]);

  return (
    <canvas
      ref={canvasRef}
      onClick={handleCanvasClick}
      className={`absolute inset-0 w-full h-full z-10 ${onSelectCandidate ? 'cursor-pointer' : 'pointer-events-none'}`}
    />
  );
}



