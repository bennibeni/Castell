export const COMPOSITION_EVENT = "castell:composition-changed";

export const BODIES = [
  {
    id: "mannequin",
    label: "Manichino Castell",
    description: "Corpo articolato con divisa. Mantiene i colori per ruolo.",
    url: "/models/catalog/body-mannequin.glb",
    image: "/previews/body-mannequin-original.png",
    headScale: 0.9,
    headY: 1.58 - 1.553 * 0.9,
  },
  {
    id: "adult",
    label: "Base anatomica adulta",
    description: "Corpo continuo animabile, pelle dal colorito roseo.",
    url: "/models/catalog/body-adult.glb",
    image: "/previews/body-adult-rosy.png",
    headScale: 1,
    headY: 0,
    skinTint: [1, 0.88, 0.91],
  },
];
export const HEADS = [
  {
    id: "mannequin-original",
    label: "Testa del manichino originale",
    description:
      "Testa geometrica originale con capelli semplici e chignon, senza texture.",
    url: "/models/catalog/head-mannequin-original.glb",
    image: "/previews/head-mannequin-original.png",
    bodies: ["mannequin", "adult"],
  },
  {
    id: "mannequin-detailed-small",
    label: "Hinako - Realistic girl",
    description:
      "La precedente testa piccola, con viso, occhi, ciglia e capelli dettagliati.",
    url: "/models/catalog/head-detailed-small-optimized.glb",
    image: "/previews/head-detailed-small.png",
    bodies: ["mannequin", "adult"],
    transform: { scale: 0.9034934067618628, offsetY: 0.1431342506173896 },
  },
];
export const DEFAULT_COMPOSITION = {
  bodyId: "mannequin",
  headId: "mannequin-original",
};
export function compatible(bodyId, headId) {
  return (
    BODIES.some((body) => body.id === bodyId) &&
    !!HEADS.find((head) => head.id === headId)?.bodies.includes(bodyId)
  );
}
export function normalizeComposition(value) {
  const body = BODIES.find((item) => item.id === value?.bodyId);
  if (!body) return { ...DEFAULT_COMPOSITION };
  const legacyHeads = {
    hinako: "mannequin-original",
    "hinako-small": "mannequin-detailed-small",
    "mannequin-original-small": "mannequin-detailed-small",
    "adult-original": "mannequin-original",
    "adult-smile": "mannequin-original",
  };
  const requested = legacyHeads[value?.headId] ?? value?.headId;
  const head =
    HEADS.find(
      (item) => item.id === requested && item.bodies.includes(body.id),
    ) ?? HEADS.find((item) => item.bodies.includes(body.id));
  return head
    ? { bodyId: body.id, headId: head.id }
    : { ...DEFAULT_COMPOSITION };
}
