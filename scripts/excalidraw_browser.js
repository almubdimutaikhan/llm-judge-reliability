import {
  convertToExcalidrawElements,
  exportToBlob,
  exportToSvg,
  serializeAsJSON,
} from "@excalidraw/excalidraw";

window.ready = (async () => {
  const font = new FontFace("Virgil", "url('/assets/fonts/Virgil/Virgil-Regular.woff2')");
  document.fonts.add(await font.load());
  await document.fonts.ready;
})();

window.renderResearchFigure = async (spec) => {
  await window.ready;
  const elements = convertToExcalidrawElements(spec.elements, { regenerateIds: false });
  for (const el of elements) {
    // Excalidraw measures the real handwriting font before placing text anchors.
    const anchor = el.customData;
    if (el.type === "text" && anchor?.align === "center") el.x = anchor.anchorX - el.width / 2;
    if (el.type === "text" && anchor?.align === "right") el.x = anchor.anchorX - el.width;
    el.versionNonce = el.seed;
    el.updated = 1;
  }
  const appState = {
    viewBackgroundColor: "#ffffff",
    exportBackground: true,
    exportWithDarkMode: false,
    exportEmbedScene: true,
    currentItemFontFamily: 1,
    gridSize: null,
  };
  const scene = JSON.parse(serializeAsJSON(elements, appState, {}, "local"));
  scene.source = "https://github.com/almubdimutaikhan/llm-judge-reliability";
  const svg = await exportToSvg({ elements, appState, files: {}, exportPadding: 16 });
  const blob = await exportToBlob({
    elements, appState, files: {}, exportPadding: 16,
    mimeType: "image/png", getDimensions: (width, height) => ({ width: width * 1.5, height: height * 1.5, scale: 1.5 }),
  });
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  const outside = elements.filter(el => el.type === "text" &&
    (el.x < 0 || el.y < 0 || el.x + el.width > spec.width || el.y + el.height > spec.height))
    .map(el => ({ id: el.id, text: el.text, x: el.x, y: el.y, width: el.width, height: el.height }));
  return {
    scene: JSON.stringify(scene, null, 2) + "\n",
    svg: new XMLSerializer().serializeToString(svg),
    png: btoa(binary),
    outside,
  };
};
