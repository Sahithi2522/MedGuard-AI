"use strict";
(() => {
  // node_modules/lucide/dist/esm/defaultAttributes.mjs
  var defaultAttributes = {
    xmlns: "http://www.w3.org/2000/svg",
    width: 24,
    height: 24,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": 2,
    "stroke-linecap": "round",
    "stroke-linejoin": "round"
  };

  // node_modules/lucide/dist/esm/createElement.mjs
  var createSVGElement = ([tag, attrs, children]) => {
    const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.keys(attrs).forEach((name) => {
      element.setAttribute(name, String(attrs[name]));
    });
    if (children?.length) {
      children.forEach((child) => {
        const childElement = createSVGElement(child);
        element.appendChild(childElement);
      });
    }
    return element;
  };
  var createElement = (iconNode, customAttrs = {}) => {
    const tag = "svg";
    const attrs = {
      ...defaultAttributes,
      ...customAttrs
    };
    return createSVGElement([tag, attrs, iconNode]);
  };

  // node_modules/lucide/dist/esm/shared/src/utils/mergeClasses.mjs
  var mergeClasses = (...classes) => classes.filter((className, index, array) => {
    return Boolean(className) && className.trim() !== "" && array.indexOf(className) === index;
  }).join(" ").trim();

  // node_modules/lucide/dist/esm/shared/src/utils/hasA11yProp.mjs
  var hasA11yProp = (props) => {
    for (const prop in props) {
      if (prop.startsWith("aria-") || prop === "role" || prop === "title") {
        return true;
      }
    }
    return false;
  };

  // node_modules/lucide/dist/esm/shared/src/utils/toCamelCase.mjs
  var toCamelCase = (string) => {
    let out = "";
    let upperNext = false;
    for (const ch of string) {
      if (ch === "-" || ch === "_" || ch <= " ") {
        upperNext = out.length > 0;
        continue;
      }
      if (out.length === 0) {
        out += ch.toLowerCase();
      } else {
        out += upperNext ? ch.toUpperCase() : ch;
      }
      upperNext = false;
    }
    return out;
  };

  // node_modules/lucide/dist/esm/shared/src/utils/toPascalCase.mjs
  var toPascalCase = (string) => {
    const camelCase = toCamelCase(string);
    return camelCase.charAt(0).toUpperCase() + camelCase.slice(1);
  };

  // node_modules/lucide/dist/esm/replaceElement.mjs
  var getAttrs = (element) => Array.from(element.attributes).reduce((attrs, attr) => {
    attrs[attr.name] = attr.value;
    return attrs;
  }, {});
  var getClassNames = (attrs) => {
    if (typeof attrs === "string") return attrs;
    if (!attrs || !attrs.class) return "";
    if (attrs.class && typeof attrs.class === "string") {
      return attrs.class.split(" ");
    }
    if (attrs.class && Array.isArray(attrs.class)) {
      return attrs.class;
    }
    return "";
  };
  var replaceElement = (element, { nameAttr, icons, attrs }) => {
    const iconName = element.getAttribute(nameAttr);
    if (iconName == null) return;
    const ComponentName = toPascalCase(iconName);
    const iconNode = icons[ComponentName];
    if (!iconNode) {
      return console.warn(
        `${element.outerHTML} icon name was not found in the provided icons object.`
      );
    }
    const elementAttrs = getAttrs(element);
    const ariaProps = hasA11yProp(elementAttrs) ? {} : { "aria-hidden": "true" };
    const iconAttrs = {
      ...defaultAttributes,
      "data-lucide": iconName,
      ...ariaProps,
      ...attrs,
      ...elementAttrs
    };
    const elementClassNames = getClassNames(elementAttrs);
    const className = getClassNames(attrs);
    const classNames = mergeClasses(
      "lucide",
      `lucide-${iconName}`,
      ...elementClassNames,
      ...className
    );
    if (classNames) {
      Object.assign(iconAttrs, {
        class: classNames
      });
    }
    const svgElement = createElement(iconNode, iconAttrs);
    return element.parentNode?.replaceChild(svgElement, element);
  };

  // node_modules/lucide/dist/esm/icons/activity.mjs
  var Activity = [
    [
      "path",
      {
        d: "M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"
      }
    ]
  ];

  // node_modules/lucide/dist/esm/icons/heart-pulse.mjs
  var HeartPulse = [
    [
      "path",
      {
        d: "M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5"
      }
    ],
    ["path", { d: "M3.22 13H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27" }]
  ];

  // node_modules/lucide/dist/esm/icons/shield-check.mjs
  var ShieldCheck = [
    [
      "path",
      {
        d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"
      }
    ],
    ["path", { d: "m9 12 2 2 4-4" }]
  ];

  // node_modules/lucide/dist/esm/icons/sparkles.mjs
  var Sparkles = [
    [
      "path",
      {
        d: "M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"
      }
    ],
    ["path", { d: "M20 2v4" }],
    ["path", { d: "M22 4h-4" }],
    ["circle", { cx: "4", cy: "20", r: "2" }]
  ];

  // node_modules/lucide/dist/esm/lucide.mjs
  var createIcons = ({
    icons = {},
    nameAttr = "data-lucide",
    attrs = {},
    root = document,
    inTemplates
  } = {}) => {
    if (!Object.values(icons).length) {
      throw new Error(
        "Please provide an icons object.\nIf you want to use all the icons you can import it like:\n `import { createIcons, icons } from 'lucide';\nlucide.createIcons({icons});`"
      );
    }
    if (typeof root === "undefined") {
      throw new Error("`createIcons()` only works in a browser environment.");
    }
    const elementsToReplace = Array.from(root.querySelectorAll(`[${nameAttr}]`));
    elementsToReplace.forEach((element) => replaceElement(element, { nameAttr, icons, attrs }));
    if (inTemplates) {
      const templates = Array.from(root.querySelectorAll("template"));
      templates.forEach(
        (template) => createIcons({
          icons,
          nameAttr,
          attrs,
          root: template.content,
          inTemplates
        })
      );
    }
    if (nameAttr === "data-lucide") {
      const deprecatedElements = root.querySelectorAll("[icon-name]");
      if (deprecatedElements.length > 0) {
        console.warn(
          "[Lucide] Some icons were found with the now deprecated icon-name attribute. These will still be replaced for backwards compatibility, but will no longer be supported in v1.0 and you should switch to data-lucide"
        );
        Array.from(deprecatedElements).forEach(
          (element) => replaceElement(element, { nameAttr: "icon-name", icons, attrs })
        );
      }
    }
  };

  // src/decorations.ts
  var iconSet = { Activity, HeartPulse, ShieldCheck, Sparkles };
  var assetBase = new URL(".", document.currentScript?.baseURI ?? location.href);
  function mountMedicalVideoBackground() {
    if (document.querySelector(".medical-video-background")) return;
    const shell = document.createElement("div");
    shell.className = "medical-video-background";
    const video = document.createElement("video");
    video.src = new URL("assetsmedical-background.mp4", assetBase).href;
    video.autoplay = true;
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.preload = "auto";
    video.tabIndex = -1;
    video.setAttribute("disablepictureinpicture", "");
    video.setAttribute("aria-hidden", "true");
    const attemptPlayback = () => {
      void video.play().then(() => shell.classList.remove("needs-play")).catch(() => shell.classList.add("needs-play"));
    };
    const startButton = document.createElement("button");
    startButton.className = "video-background-start";
    startButton.type = "button";
    startButton.textContent = "Play background video";
    startButton.addEventListener("click", () => {
      void video.play().then(() => shell.classList.remove("needs-play")).catch(() => void 0);
    });
    video.addEventListener("loadeddata", () => {
      if (video.videoWidth && video.videoHeight) {
        const canvas = document.createElement("canvas");
        const width = Math.min(720, video.videoWidth);
        const height = Math.round(width * video.videoHeight / video.videoWidth);
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d");
        if (context) {
          context.drawImage(video, 0, 0, width, height);
          video.poster = canvas.toDataURL("image/jpeg", 0.76);
        }
      }
    }, { once: true });
    video.addEventListener("canplay", attemptPlayback, { once: true });
    shell.append(video, startButton);
    document.body.prepend(shell);
    attemptPlayback();
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible" && video.paused) attemptPlayback();
    });
  }
  function mountLandingDecoration() {
    const hero = document.querySelector(".hero-copy");
    if (!hero || hero.querySelector(".clinical-ribbon")) return;
    const ribbon = document.createElement("aside");
    ribbon.className = "clinical-ribbon";
    ribbon.setAttribute("aria-label", "Clinical reference status");
    ribbon.innerHTML = `
    <span class="clinical-ribbon__icon"><i data-lucide="activity"></i></span>
    <span class="clinical-ribbon__copy"><strong>REFERENCE STATUS</strong><small>Clinical data is not configured in this demo</small></span>
    <span class="clinical-ribbon__bars" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>
  `;
    hero.append(ribbon);
  }
  function mountWorkspaceDecoration() {
    const heading = document.querySelector(".page-heading > div");
    if (!heading || heading.querySelector(".workspace-ribbon")) return;
    const ribbon = document.createElement("div");
    ribbon.className = "workspace-ribbon";
    ribbon.innerHTML = `
    <span class="workspace-ribbon__icon"><i data-lucide="shield-check"></i></span>
    <span><strong>DEMO WORKSPACE</strong><small>Reference coverage: limited</small></span>
    <i class="workspace-ribbon__sparkle" data-lucide="sparkles" aria-hidden="true"></i>
  `;
    heading.append(ribbon);
  }
  function mountDecorativeIcons() {
    createIcons({ icons: iconSet });
  }
  function decorate() {
    mountMedicalVideoBackground();
    mountLandingDecoration();
    mountWorkspaceDecoration();
    mountDecorativeIcons();
  }
  function startDecorations() {
    decorate();
    const app = document.getElementById("app");
    if (!app) return;
    const observer = new MutationObserver(() => {
      window.requestAnimationFrame(decorate);
    });
    observer.observe(app, { childList: true, subtree: true });
  }
  var style = document.createElement("style");
  style.textContent = `
  :root{--ink:#081c26;--muted:#405a64;--teal:#066861;--teal-dark:#034c49;--mint:#c4e5dc;--blue:#bfd7e2;--paper:#dce9e7;--line:rgba(13,55,61,.22);--glass:rgba(220,234,230,.91);--shadow:0 18px 55px rgba(8,32,40,.22)}
  .medical-video-background{position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none;background:#0b2731}
  .medical-video-background::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(224,243,240,.18),rgba(224,243,240,.05) 48%,rgba(224,243,240,.16)),linear-gradient(180deg,rgba(228,244,241,.3),rgba(4,24,32,.04))}
  .medical-video-background video{position:absolute;inset:-8%;width:116%;height:116%;object-fit:cover;opacity:.94;filter:saturate(.76) contrast(1.02) brightness(1.08)}
  .sidebar{background:rgba(215,231,228,.88);border-right-color:rgba(13,55,61,.2)}
  .side-nav a{color:#3f5b64}
  .side-nav a:hover,.side-nav a.active{background:rgba(143,193,180,.5);color:#034c49}
  .brand-mark{background:linear-gradient(140deg,#075c59,#168b7e);box-shadow:0 7px 18px rgba(4,51,54,.3)}
  .btn-primary{background:#066861;box-shadow:0 8px 20px rgba(4,61,59,.28)}
  .btn-primary:hover{background:#034c49}
  .eyebrow{color:#075c59}
  .video-background-start{display:none;position:fixed;right:16px;bottom:16px;z-index:3;padding:10px 14px;border:1px solid rgba(255,255,255,.9);border-radius:10px;background:#087f79;color:white;font:600 12px "Segoe UI",sans-serif;box-shadow:0 5px 18px rgba(21,49,61,.2);pointer-events:auto;cursor:pointer}
  .medical-video-background.needs-play .video-background-start{display:block}
  #app{position:relative;z-index:1}
  .clinical-ribbon,.workspace-ribbon{display:flex;align-items:center;gap:11px;border:1px solid rgba(8,74,73,.22);background:rgba(220,234,230,.9);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
  .clinical-ribbon{width:max-content;max-width:100%;margin-top:20px;padding:9px 12px;border-radius:14px;animation:ribbon-arrive .55s ease both}
  .clinical-ribbon__icon,.workspace-ribbon__icon{display:grid;place-items:center;flex:none;width:30px;height:30px;border-radius:10px;background:linear-gradient(145deg,#dff4ed,#e5f1f7);color:#087f79}
  .clinical-ribbon__icon svg,.workspace-ribbon__icon svg{width:16px;height:16px;stroke-width:1.8}
  .clinical-ribbon__copy strong,.workspace-ribbon strong{display:block;color:#315963;font-size:9px;letter-spacing:.8px}
  .clinical-ribbon__copy small,.workspace-ribbon small{display:block;color:#738991;font-size:10px;margin-top:3px}
  .clinical-ribbon__bars{height:19px;display:flex;align-items:center;gap:3px;margin-left:7px}
  .clinical-ribbon__bars i{width:3px;height:6px;border-radius:3px;background:#57ad9e;animation:pulse-bar 1.15s ease-in-out infinite alternate}
  .clinical-ribbon__bars i:nth-child(2),.clinical-ribbon__bars i:nth-child(6){height:11px;animation-delay:.12s}
  .clinical-ribbon__bars i:nth-child(3),.clinical-ribbon__bars i:nth-child(5){height:15px;animation-delay:.24s}
  .clinical-ribbon__bars i:nth-child(4){height:19px;animation-delay:.36s}
  .workspace-ribbon{gap:8px;margin-top:11px;padding:7px 10px;border-radius:13px;align-self:flex-start;white-space:nowrap}
  .workspace-ribbon__icon{width:27px;height:27px}
  .workspace-ribbon__icon svg{width:15px;height:15px}
  .workspace-ribbon strong{font-size:8px}
  .workspace-ribbon small{font-size:9px}
  .workspace-ribbon__sparkle{width:13px;height:13px;color:#4c9f91;margin-left:3px}
  .feature,.feature-item,.metric,.panel{transition:transform .2s ease,box-shadow .2s ease}
  .feature:hover,.feature-item:hover,.metric:hover{transform:translateY(-2px);box-shadow:0 18px 38px rgba(31,83,87,.12)}
  @keyframes pulse-bar{to{opacity:.42;transform:scaleY(.58)}}
  @keyframes ribbon-arrive{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
  @media(max-width:680px){.workspace-ribbon{gap:6px;padding:6px 7px}.workspace-ribbon__sparkle{display:none}.workspace-ribbon small{max-width:104px;white-space:normal}.clinical-ribbon{gap:8px}.clinical-ribbon__copy small{max-width:175px;line-height:1.35}.medical-video-background video{opacity:.9;filter:saturate(.74) contrast(1.02) brightness(1.1)}.medical-video-background::after{background:linear-gradient(90deg,rgba(224,243,240,.16),rgba(224,243,240,.04) 48%,rgba(224,243,240,.14)),linear-gradient(180deg,rgba(228,244,241,.28),rgba(4,24,32,.04))}}
  @media(prefers-reduced-motion:reduce){.clinical-ribbon,.clinical-ribbon__bars i{animation:none!important}.feature,.feature-item,.metric,.panel{transition:none}}
`;
  document.head.append(style);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startDecorations, { once: true });
  } else {
    startDecorations();
  }
})();
/*! Bundled license information:

lucide/dist/esm/defaultAttributes.mjs:
lucide/dist/esm/createElement.mjs:
lucide/dist/esm/shared/src/utils/mergeClasses.mjs:
lucide/dist/esm/shared/src/utils/hasA11yProp.mjs:
lucide/dist/esm/shared/src/utils/toCamelCase.mjs:
lucide/dist/esm/shared/src/utils/toPascalCase.mjs:
lucide/dist/esm/replaceElement.mjs:
lucide/dist/esm/icons/activity.mjs:
lucide/dist/esm/icons/heart-pulse.mjs:
lucide/dist/esm/icons/shield-check.mjs:
lucide/dist/esm/icons/sparkles.mjs:
lucide/dist/esm/lucide.mjs:
  (**
   * @license lucide v1.48.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)
*/
