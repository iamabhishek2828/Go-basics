import React, { Suspense, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import {
  ContactShadows,
  Environment,
  Html,
  useGLTF,
} from "@react-three/drei";
import * as SkeletonUtils from "three/examples/jsm/utils/SkeletonUtils.js";
import * as THREE from "three";

const DEFAULT_RPM_FEMALE_AVATAR_URL =
  "/subsurface_scattering_sss_demo_lara.glb";
const AVATAR_MODE = import.meta.env.VITE_AVATAR_MODE || "glb";
const AVATAR_GLB_URL =
  import.meta.env.VITE_AVATAR_GLB_URL || DEFAULT_RPM_FEMALE_AVATAR_URL;

const ALL_RPM_VISEMES = [
  "viseme_sil",
  "viseme_PP",
  "viseme_FF",
  "viseme_TH",
  "viseme_DD",
  "viseme_kk",
  "viseme_CH",
  "viseme_SS",
  "viseme_nn",
  "viseme_RR",
  "viseme_aa",
  "viseme_E",
  "viseme_I",
  "viseme_O",
  "viseme_U",
];

const ARKIT_FALLBACK_MAP = {
  viseme_PP: ["mouthPressLeft", "mouthPressRight"],
  viseme_FF: ["mouthFunnel"],
  viseme_TH: ["tongueOut", "jawOpen"],
  viseme_DD: ["jawOpen"],
  viseme_kk: ["jawOpen"],
  viseme_CH: ["mouthPucker"],
  viseme_SS: ["mouthStretchLeft", "mouthStretchRight"],
  viseme_nn: ["jawOpen"],
  viseme_RR: ["mouthPucker"],
  viseme_aa: ["jawOpen"],
  viseme_E: ["mouthSmileLeft", "mouthSmileRight"],
  viseme_I: ["mouthSmileLeft", "mouthSmileRight"],
  viseme_O: ["mouthFunnel"],
  viseme_U: ["mouthPucker"],
};

const ALL_ARKIT_FALLBACK_MORPHS = [...new Set(Object.values(ARKIT_FALLBACK_MAP).flat())];
const BLINK_MORPHS = [
  ["eyeBlinkLeft", "EyeBlinkLeft"],
  ["eyeBlinkRight", "EyeBlinkRight"],
  ["eyesClosed", "EyesClosed"],
];
const JAW_BONE_PATTERN = /jaw|chin|mandible/i;
const MOUTH_MESH_PATTERN = /mouth|lip|teeth|tongue/i;
const FACE_MESH_PATTERN = /head|face/i;

const DEFAULT_CAMERA_POSITION = new THREE.Vector3(0, 1.42, 1.55);
const LOOK_AT_TARGET = new THREE.Vector3(0, 1.3, 0);
const GLB_JSON_CHUNK_TYPE = 0x4e4f534a;
const GLB_BIN_CHUNK_TYPE = 0x004e4942;

function parseGLB(arrayBuffer) {
  const dataView = new DataView(arrayBuffer);
  const totalLength = dataView.getUint32(8, true);
  let offset = 12;
  let jsonChunk = null;
  let binChunk = null;

  while (offset < totalLength) {
    const chunkLength = dataView.getUint32(offset, true);
    const chunkType = dataView.getUint32(offset + 4, true);
    const chunkStart = offset + 8;
    const chunkEnd = chunkStart + chunkLength;
    const chunkData = arrayBuffer.slice(chunkStart, chunkEnd);

    if (chunkType === GLB_JSON_CHUNK_TYPE) {
      jsonChunk = JSON.parse(new TextDecoder().decode(chunkData));
    } else if (chunkType === GLB_BIN_CHUNK_TYPE) {
      binChunk = chunkData;
    }

    offset = chunkEnd;
  }

  return { jsonChunk, binChunk };
}

async function loadLegacySpecGlossMaterials(avatarUrl) {
  const response = await fetch(avatarUrl);

  if (!response.ok) {
    throw new Error(`Avatar request failed with status ${response.status}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  const { jsonChunk, binChunk } = parseGLB(arrayBuffer);

  if (
    !jsonChunk ||
    !binChunk ||
    !(jsonChunk.extensionsUsed || []).includes(
      "KHR_materials_pbrSpecularGlossiness"
    )
  ) {
    return { materialMap: null, cleanup: () => {} };
  }

  const textureLoader = new THREE.TextureLoader();
  const textureCache = new Map();
  const objectUrls = [];
  const materialMap = new Map();

  const loadTexture = async (textureInfo) => {
    if (!textureInfo) {
      return null;
    }

    const textureIndex = textureInfo.index;
    if (textureCache.has(textureIndex)) {
      return textureCache.get(textureIndex);
    }

    const textureDef = jsonChunk.textures?.[textureIndex];
    const imageDef = jsonChunk.images?.[textureDef?.source];
    const bufferViewDef = jsonChunk.bufferViews?.[imageDef?.bufferView];

    if (!textureDef || !imageDef || !bufferViewDef) {
      return null;
    }

    const byteOffset = bufferViewDef.byteOffset || 0;
    const byteLength = bufferViewDef.byteLength || 0;
    const imageBytes = binChunk.slice(byteOffset, byteOffset + byteLength);
    const objectUrl = URL.createObjectURL(
      new Blob([imageBytes], {
        type: imageDef.mimeType || "application/octet-stream",
      })
    );

    objectUrls.push(objectUrl);

    const texture = await textureLoader.loadAsync(objectUrl);
    texture.flipY = false;
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.needsUpdate = true;
    textureCache.set(textureIndex, texture);
    return texture;
  };

  for (const materialDef of jsonChunk.materials || []) {
    const legacyExtension =
      materialDef.extensions?.KHR_materials_pbrSpecularGlossiness;

    if (!legacyExtension) {
      continue;
    }

    materialMap.set(materialDef.name, {
      alphaMode: materialDef.alphaMode || "OPAQUE",
      diffuseFactor: legacyExtension.diffuseFactor || [1, 1, 1, 1],
      glossinessFactor: legacyExtension.glossinessFactor ?? 0.5,
      map: await loadTexture(legacyExtension.diffuseTexture),
    });
  }

  return {
    materialMap,
    cleanup: () => {
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
      textureCache.forEach((texture) => texture.dispose());
    },
  };
}

function getActiveViseme(visemes, audioRef, isSpeaking) {
  if (!isSpeaking || !audioRef.current || visemes.length === 0) {
    return { viseme: "viseme_sil", value: 0 };
  }

  const currentTimeMs = audioRef.current.currentTime * 1000;
  let activeViseme = visemes[0];

  for (let index = 0; index < visemes.length; index += 1) {
    if (visemes[index].time <= currentTimeMs) {
      activeViseme = visemes[index];
    } else {
      break;
    }
  }

  return activeViseme;
}

function updateInfluence(mesh, morphName, targetValue, smoothing = 0.18) {
  const index = mesh.morphTargetDictionary?.[morphName];

  if (index === undefined) {
    return false;
  }

  mesh.morphTargetInfluences[index] = THREE.MathUtils.lerp(
    mesh.morphTargetInfluences[index],
    targetValue,
    smoothing
  );

  return true;
}

function updateFirstAvailableInfluence(mesh, morphNames, targetValue, smoothing = 0.18) {
  morphNames.some((morphName) =>
    updateInfluence(mesh, morphName, targetValue, smoothing)
  );
}

function LoadingAvatar() {
  return (
    <Html center>
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading 3D avatar...</p>
      </div>
    </Html>
  );
}

function ProceduralAvatar({ visemes, isSpeaking, audioRef }) {
  const groupRef = useRef();
  const jawRef = useRef();
  const upperLipRef = useRef();
  const lowerLipRef = useRef();
  const mouthInteriorRef = useRef();
  const leftEyeRef = useRef();
  const rightEyeRef = useRef();
  const leftPupilRef = useRef();
  const rightPupilRef = useRef();
  const blinkRef = useRef({ timer: 0, nextBlink: 3, isBlinking: false, progress: 0 });
  const mouthRef = useRef({ jawOpen: 0, mouthWidth: 0, lipRound: 0 });

  const skinMaterial = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#f5cba7", roughness: 0.6, metalness: 0.05 }),
    []
  );
  const lipMaterial = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#c0392b", roughness: 0.4, metalness: 0.05 }),
    []
  );
  const eyeWhiteMaterial = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#fdfefe", roughness: 0.3 }),
    []
  );
  const hairMaterial = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#1a1a2e", roughness: 0.7, metalness: 0.1 }),
    []
  );
  const shirtMaterial = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#00843d", roughness: 0.5, metalness: 0.05 }),
    []
  );
  const blazerMaterial = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#1a2332", roughness: 0.6, metalness: 0.05 }),
    []
  );
  const mouthInteriorMat = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#8b0000", roughness: 0.8 }),
    []
  );

  useFrame((state, delta) => {
    const activeViseme = getActiveViseme(visemes, audioRef, isSpeaking);
    const blink = blinkRef.current;
    const mouth = mouthRef.current;
    const simpleShapes = {
      viseme_sil: [0.0, 0.0, 0.0],
      viseme_PP: [0.0, 0.0, 0.1],
      viseme_FF: [0.05, 0.1, 0.0],
      viseme_TH: [0.1, 0.1, 0.0],
      viseme_DD: [0.15, 0.05, 0.0],
      viseme_kk: [0.2, 0.0, 0.0],
      viseme_CH: [0.1, 0.05, 0.2],
      viseme_SS: [0.05, 0.15, 0.0],
      viseme_nn: [0.1, 0.0, 0.0],
      viseme_RR: [0.15, 0.0, 0.1],
      viseme_aa: [0.5, 0.1, 0.0],
      viseme_E: [0.3, 0.2, 0.0],
      viseme_I: [0.15, 0.25, 0.0],
      viseme_O: [0.35, 0.0, 0.4],
      viseme_U: [0.2, 0.0, 0.5],
    };

    const shape = simpleShapes[activeViseme.viseme] || simpleShapes.viseme_sil;
    const targetJaw = shape[0] * (activeViseme.value || 0);
    const targetWidth = shape[1] * (activeViseme.value || 0);
    const targetRound = shape[2] * (activeViseme.value || 0);

    mouth.jawOpen = THREE.MathUtils.lerp(mouth.jawOpen, targetJaw, 0.25);
    mouth.mouthWidth = THREE.MathUtils.lerp(mouth.mouthWidth, targetWidth, 0.25);
    mouth.lipRound = THREE.MathUtils.lerp(mouth.lipRound, targetRound, 0.25);

    if (jawRef.current) {
      jawRef.current.position.y = -0.04 - mouth.jawOpen * 0.08;
      jawRef.current.scale.x = 1 + mouth.mouthWidth * 0.3 - mouth.lipRound * 0.2;
    }
    if (upperLipRef.current) {
      upperLipRef.current.scale.x = 1 + mouth.mouthWidth * 0.3 - mouth.lipRound * 0.2;
      upperLipRef.current.position.y = 0.002 + mouth.jawOpen * 0.01;
    }
    if (lowerLipRef.current) {
      lowerLipRef.current.scale.x = 1 + mouth.mouthWidth * 0.3 - mouth.lipRound * 0.2;
      lowerLipRef.current.position.y = -0.04 - mouth.jawOpen * 0.06;
    }
    if (mouthInteriorRef.current) {
      mouthInteriorRef.current.scale.y = Math.max(0.1, mouth.jawOpen * 2);
      mouthInteriorRef.current.scale.x = 1 + mouth.mouthWidth * 0.3 - mouth.lipRound * 0.2;
      mouthInteriorRef.current.visible = mouth.jawOpen > 0.02;
    }

    blink.timer += delta;

    if (!blink.isBlinking && blink.timer >= blink.nextBlink) {
      blink.isBlinking = true;
      blink.progress = 0;
    }

    if (blink.isBlinking) {
      blink.progress += delta * 8;
      let blinkValue;

      if (blink.progress < 0.5) {
        blinkValue = blink.progress * 2;
      } else if (blink.progress < 1.0) {
        blinkValue = 2 - blink.progress * 2;
      } else {
        blinkValue = 0;
        blink.isBlinking = false;
        blink.timer = 0;
        blink.nextBlink = 2 + Math.random() * 4;
      }

      if (leftEyeRef.current) leftEyeRef.current.scale.y = 1 - blinkValue * 0.9;
      if (rightEyeRef.current) rightEyeRef.current.scale.y = 1 - blinkValue * 0.9;
      if (leftPupilRef.current) leftPupilRef.current.scale.y = 1 - blinkValue * 0.9;
      if (rightPupilRef.current) rightPupilRef.current.scale.y = 1 - blinkValue * 0.9;
    }

    if (groupRef.current) {
      const breathe = Math.sin(state.clock.elapsedTime * 1.2) * 0.003;
      const sway = Math.sin(state.clock.elapsedTime * 0.5) * 0.005;
      groupRef.current.position.y = breathe;
      groupRef.current.rotation.z = sway;
      groupRef.current.rotation.x = isSpeaking
        ? Math.sin(state.clock.elapsedTime * 2) * 0.02
        : THREE.MathUtils.lerp(groupRef.current.rotation.x, 0, 0.05);
    }
  });

  return (
    <group ref={groupRef} position={[0, -0.2, 0]}>
      <group position={[0, 0.55, 0]}>
        <mesh material={skinMaterial}>
          <sphereGeometry args={[0.22, 32, 32]} />
        </mesh>

        <mesh position={[-0.21, 0, 0]} material={skinMaterial}>
          <sphereGeometry args={[0.035, 16, 16]} />
        </mesh>
        <mesh position={[0.21, 0, 0]} material={skinMaterial}>
          <sphereGeometry args={[0.035, 16, 16]} />
        </mesh>

        <mesh position={[0, 0.08, -0.02]} material={hairMaterial}>
          <sphereGeometry args={[0.23, 32, 32]} />
        </mesh>
        <mesh position={[-0.18, -0.02, -0.04]} material={hairMaterial}>
          <sphereGeometry args={[0.1, 16, 16]} />
        </mesh>
        <mesh position={[0.18, -0.02, -0.04]} material={hairMaterial}>
          <sphereGeometry args={[0.1, 16, 16]} />
        </mesh>
        <mesh position={[0, -0.08, -0.12]} material={hairMaterial}>
          <sphereGeometry args={[0.18, 16, 16]} />
        </mesh>
        <mesh position={[0, -0.05, -0.18]} material={hairMaterial}>
          <sphereGeometry args={[0.1, 16, 16]} />
        </mesh>

        <group position={[-0.075, 0.03, 0.18]}>
          <mesh ref={leftEyeRef} material={eyeWhiteMaterial}>
            <sphereGeometry args={[0.035, 16, 16]} />
          </mesh>
          <mesh ref={leftPupilRef} position={[0, 0, 0.025]}>
            <sphereGeometry args={[0.02, 16, 16]} />
            <meshStandardMaterial color="#6b4226" roughness={0.3} />
          </mesh>
          <mesh position={[0, 0, 0.032]}>
            <sphereGeometry args={[0.01, 16, 16]} />
            <meshStandardMaterial color="#0a0a0a" roughness={0.2} />
          </mesh>
        </group>

        <group position={[0.075, 0.03, 0.18]}>
          <mesh ref={rightEyeRef} material={eyeWhiteMaterial}>
            <sphereGeometry args={[0.035, 16, 16]} />
          </mesh>
          <mesh ref={rightPupilRef} position={[0, 0, 0.025]}>
            <sphereGeometry args={[0.02, 16, 16]} />
            <meshStandardMaterial color="#6b4226" roughness={0.3} />
          </mesh>
          <mesh position={[0, 0, 0.032]}>
            <sphereGeometry args={[0.01, 16, 16]} />
            <meshStandardMaterial color="#0a0a0a" roughness={0.2} />
          </mesh>
        </group>

        <mesh position={[-0.075, 0.075, 0.19]} rotation={[0, 0, 0.15]} material={hairMaterial}>
          <boxGeometry args={[0.06, 0.008, 0.01]} />
        </mesh>
        <mesh position={[0.075, 0.075, 0.19]} rotation={[0, 0, -0.15]} material={hairMaterial}>
          <boxGeometry args={[0.06, 0.008, 0.01]} />
        </mesh>

        <mesh position={[0, -0.01, 0.21]} material={skinMaterial}>
          <sphereGeometry args={[0.018, 12, 12]} />
        </mesh>
        <mesh position={[0, -0.02, 0.22]} material={skinMaterial} rotation={[0.3, 0, 0]}>
          <sphereGeometry args={[0.012, 12, 12]} />
        </mesh>

        <group position={[0, -0.06, 0.19]}>
          <mesh ref={mouthInteriorRef} position={[0, -0.015, -0.005]} material={mouthInteriorMat} visible={false}>
            <boxGeometry args={[0.05, 0.03, 0.02]} />
          </mesh>
          <mesh ref={upperLipRef} position={[0, 0.002, 0]} material={lipMaterial}>
            <boxGeometry args={[0.055, 0.012, 0.015]} />
          </mesh>
          <mesh ref={lowerLipRef} position={[0, -0.015, 0]} material={lipMaterial}>
            <boxGeometry args={[0.05, 0.014, 0.015]} />
          </mesh>
        </group>
      </group>

      <mesh position={[0, 0.3, 0]} material={skinMaterial}>
        <cylinderGeometry args={[0.06, 0.07, 0.08, 16]} />
      </mesh>

      <group position={[0, 0.05, 0]}>
        <mesh position={[0, 0, 0]} material={blazerMaterial}>
          <cylinderGeometry args={[0.2, 0.18, 0.4, 16]} />
        </mesh>
        <mesh position={[0, 0.17, 0.08]} material={shirtMaterial} rotation={[0.3, 0, 0]}>
          <boxGeometry args={[0.12, 0.06, 0.02]} />
        </mesh>
        <mesh position={[-0.08, 0.1, 0.14]} material={blazerMaterial} rotation={[0.2, 0.3, 0]}>
          <boxGeometry args={[0.06, 0.12, 0.01]} />
        </mesh>
        <mesh position={[0.08, 0.1, 0.14]} material={blazerMaterial} rotation={[0.2, -0.3, 0]}>
          <boxGeometry args={[0.06, 0.12, 0.01]} />
        </mesh>
        <mesh position={[0, 0.08, 0.15]} material={shirtMaterial} rotation={[0.1, 0, 0]}>
          <boxGeometry args={[0.08, 0.12, 0.005]} />
        </mesh>
        <mesh position={[-0.12, 0.12, 0.16]} material={shirtMaterial}>
          <boxGeometry args={[0.03, 0.03, 0.005]} />
        </mesh>
        <mesh position={[-0.22, 0.15, 0]} material={blazerMaterial}>
          <sphereGeometry args={[0.07, 16, 16]} />
        </mesh>
        <mesh position={[0.22, 0.15, 0]} material={blazerMaterial}>
          <sphereGeometry args={[0.07, 16, 16]} />
        </mesh>
      </group>
    </group>
  );
}

function GLBAvatarModel({ avatarUrl, visemes, isSpeaking, audioRef }) {
  const { scene } = useGLTF(avatarUrl);
  const avatarRootRef = useRef();
  const blinkRef = useRef({ timer: 0, nextBlink: 2.5, isBlinking: false, progress: 0 });
  const fakeLipRef = useRef({
    open: 0,
    audioElement: null,
    audioContext: null,
    audioSource: null,
    analyser: null,
    dataArray: null,
  });

  const { avatarScene, focusTarget, cameraPosition } = useMemo(() => {
    const clonedScene = SkeletonUtils.clone(scene);
    const box = new THREE.Box3().setFromObject(clonedScene);
    const size = new THREE.Vector3();
    box.getSize(size);
    const hasSkinnedMesh = { value: false };
    const hasMorphTargets = { value: false };

    clonedScene.traverse((object) => {
      if (object.isSkinnedMesh) {
        hasSkinnedMesh.value = true;
      }

      if (object.morphTargetDictionary && object.morphTargetInfluences) {
        hasMorphTargets.value = true;
      }
    });

    const bustLikeModel =
      !hasSkinnedMesh.value &&
      !hasMorphTargets.value &&
      size.y <= size.x * 1.6;

    const targetHeight = bustLikeModel ? 0.72 : 2.05;
    const scale = targetHeight / Math.max(size.y, 0.01);
    clonedScene.scale.setScalar(scale);

    const scaledBox = new THREE.Box3().setFromObject(clonedScene);
    const scaledCenter = new THREE.Vector3();
    scaledBox.getCenter(scaledCenter);

    clonedScene.position.x = -scaledCenter.x;
    clonedScene.position.z = -scaledCenter.z;
    clonedScene.position.y = -scaledBox.min.y - (bustLikeModel ? 0.3 : 0.08);

    clonedScene.traverse((object) => {
      if (!object.isMesh && !object.isSkinnedMesh) {
        return;
      }

      object.castShadow = true;
      object.receiveShadow = true;
      object.frustumCulled = false;

      const materials = Array.isArray(object.material)
        ? object.material
        : [object.material];

      materials.forEach((material) => {
        if (!material) {
          return;
        }

        if ("envMapIntensity" in material) {
          material.envMapIntensity = 1.15;
        }
      });
    });

    const reframedBox = new THREE.Box3().setFromObject(clonedScene);
    const reframedSize = reframedBox.getSize(new THREE.Vector3());
    const lookTarget = bustLikeModel
      ? new THREE.Vector3(0, reframedBox.min.y + reframedSize.y * 0.34, 0)
      : LOOK_AT_TARGET.clone();
    const framedCameraPosition = bustLikeModel
      ? new THREE.Vector3(0, lookTarget.y - 0.02, 2.15)
      : DEFAULT_CAMERA_POSITION.clone();

    return {
      avatarScene: clonedScene,
      focusTarget: lookTarget,
      cameraPosition: framedCameraPosition,
    };
  }, [scene]);

  const morphMeshes = useMemo(() => {
    const meshes = [];

    avatarScene.traverse((object) => {
      if (
        (object.isMesh || object.isSkinnedMesh) &&
        object.morphTargetDictionary &&
        object.morphTargetInfluences
      ) {
        meshes.push(object);
      }
    });

    return meshes;
  }, [avatarScene]);

  const hasVisemeMorphSupport = useMemo(
    () =>
      morphMeshes.some((mesh) => {
        const dictionary = mesh.morphTargetDictionary || {};

        return (
          dictionary.jawOpen !== undefined ||
          ALL_RPM_VISEMES.some((visemeName) => dictionary[visemeName] !== undefined)
        );
      }),
    [morphMeshes]
  );

  const jawBones = useMemo(() => {
    const bones = [];

    avatarScene.traverse((object) => {
      if (object.isBone && JAW_BONE_PATTERN.test(object.name || "")) {
        bones.push({
          bone: object,
          baseRotationX: object.rotation.x,
        });
      }
    });

    return bones;
  }, [avatarScene]);

  const mouthMeshes = useMemo(() => {
    const meshes = [];

    avatarScene.traverse((object) => {
      if ((object.isMesh || object.isSkinnedMesh) && MOUTH_MESH_PATTERN.test(object.name || "")) {
        meshes.push({
          mesh: object,
          baseScaleY: object.scale.y,
          basePositionY: object.position.y,
        });
      }
    });

    return meshes;
  }, [avatarScene]);

  const faceMeshes = useMemo(() => {
    const meshes = [];

    avatarScene.traverse((object) => {
      if ((object.isMesh || object.isSkinnedMesh) && FACE_MESH_PATTERN.test(object.name || "")) {
        meshes.push({
          mesh: object,
          baseScaleX: object.scale.x,
          baseScaleY: object.scale.y,
          baseScaleZ: object.scale.z,
          basePositionY: object.position.y,
          baseRotationX: object.rotation.x,
        });
      }
    });

    return meshes;
  }, [avatarScene]);

  const shouldUseFakeLipSync =
    !hasVisemeMorphSupport &&
    (jawBones.length > 0 || mouthMeshes.length > 0 || faceMeshes.length > 0);

  const disposeFakeLipSyncAudio = () => {
    const fakeLip = fakeLipRef.current;

    if (fakeLip.audioSource) {
      try {
        fakeLip.audioSource.disconnect();
      } catch (error) {
        console.debug("Fake lip source disconnect skipped:", error);
      }
    }

    if (fakeLip.analyser) {
      try {
        fakeLip.analyser.disconnect();
      } catch (error) {
        console.debug("Fake lip analyser disconnect skipped:", error);
      }
    }

    if (fakeLip.audioContext && fakeLip.audioContext.state !== "closed") {
      fakeLip.audioContext.close().catch(() => {});
    }

    fakeLip.audioElement = null;
    fakeLip.audioContext = null;
    fakeLip.audioSource = null;
    fakeLip.analyser = null;
    fakeLip.dataArray = null;
  };

  React.useEffect(() => () => {
    disposeFakeLipSyncAudio();
  }, []);

  React.useEffect(() => {
    let isActive = true;
    let cleanupLegacyMaterials = () => {};

    async function applyLegacyMaterials() {
      try {
        const { materialMap, cleanup } = await loadLegacySpecGlossMaterials(
          avatarUrl
        );

        cleanupLegacyMaterials = cleanup;

        if (!isActive || !materialMap || materialMap.size === 0) {
          return;
        }

        avatarScene.traverse((object) => {
          if (!object.isMesh && !object.isSkinnedMesh) {
            return;
          }

          const materials = Array.isArray(object.material)
            ? object.material
            : [object.material];

          materials.forEach((material) => {
            if (!material) {
              return;
            }

            const legacyMaterial = materialMap.get(material.name);
            if (!legacyMaterial) {
              return;
            }

            const [r, g, b, a] = legacyMaterial.diffuseFactor;

            material.color.setRGB(r, g, b);
            material.opacity = a;
            material.transparent =
              legacyMaterial.alphaMode === "BLEND" || a < 1;

            if (legacyMaterial.map) {
              material.map = legacyMaterial.map;
              if (legacyMaterial.alphaMode === "BLEND") {
                material.alphaMap = legacyMaterial.map;
              }
            }

            if ("metalness" in material) {
              material.metalness = 0;
            }

            if ("roughness" in material) {
              material.roughness = THREE.MathUtils.clamp(
                1 - legacyMaterial.glossinessFactor,
                0.05,
                1
              );
            }

            material.needsUpdate = true;
          });
        });
      } catch (error) {
        console.warn("Legacy GLB material fallback failed:", error);
      }
    }

    applyLegacyMaterials();

    return () => {
      isActive = false;
      cleanupLegacyMaterials();
    };
  }, [avatarScene, avatarUrl]);

  useFrame((state, delta) => {
    state.camera.position.lerp(cameraPosition, 0.08);
    state.camera.lookAt(focusTarget);

    const activeViseme = getActiveViseme(visemes, audioRef, isSpeaking);
    const blink = blinkRef.current;

    blink.timer += delta;

    if (!blink.isBlinking && blink.timer >= blink.nextBlink) {
      blink.isBlinking = true;
      blink.progress = 0;
    }

    let blinkValue = 0;

    if (blink.isBlinking) {
      blink.progress += delta * 9;

      if (blink.progress < 0.5) {
        blinkValue = blink.progress * 2;
      } else if (blink.progress < 1) {
        blinkValue = 2 - blink.progress * 2;
      } else {
        blinkValue = 0;
        blink.isBlinking = false;
        blink.timer = 0;
        blink.nextBlink = 2 + Math.random() * 3;
      }
    }

    morphMeshes.forEach((mesh) => {
      ALL_RPM_VISEMES.forEach((visemeName) => {
        const targetValue =
          activeViseme.viseme === visemeName ? activeViseme.value || 0 : 0;
        updateInfluence(mesh, visemeName, targetValue);
      });

      const fallbackMorphTargets = ARKIT_FALLBACK_MAP[activeViseme.viseme] || [];
      const mouthFallbackValue =
        activeViseme.viseme === "viseme_sil"
          ? 0
          : THREE.MathUtils.clamp((activeViseme.value || 0) * 0.55, 0, 1);

      ALL_ARKIT_FALLBACK_MORPHS.forEach((morphName) => {
        const isActive = fallbackMorphTargets.includes(morphName);
        updateInfluence(mesh, morphName, isActive ? mouthFallbackValue : 0, 0.12);
      });

      updateInfluence(
        mesh,
        "jawOpen",
        activeViseme.viseme === "viseme_sil"
          ? 0
          : THREE.MathUtils.clamp((activeViseme.value || 0) * 0.35, 0, 1),
        0.14
      );
      BLINK_MORPHS.forEach((morphNames) => {
        updateFirstAvailableInfluence(mesh, morphNames, blinkValue, 0.3);
      });
    });

    if (shouldUseFakeLipSync) {
      const fakeLip = fakeLipRef.current;
      const currentAudio = audioRef.current;

      if (
        isSpeaking &&
        currentAudio &&
        currentAudio !== fakeLip.audioElement
      ) {
        disposeFakeLipSyncAudio();

        try {
          const audioContext = new (window.AudioContext || window.webkitAudioContext)();
          const analyser = audioContext.createAnalyser();
          analyser.fftSize = 256;

          const source = audioContext.createMediaElementSource(currentAudio);
          source.connect(analyser);
          analyser.connect(audioContext.destination);

          if (audioContext.state === "suspended") {
            audioContext.resume().catch(() => {});
          }

          fakeLip.audioElement = currentAudio;
          fakeLip.audioContext = audioContext;
          fakeLip.audioSource = source;
          fakeLip.analyser = analyser;
          fakeLip.dataArray = new Uint8Array(analyser.frequencyBinCount);
        } catch (error) {
          console.warn("Fake lip-sync audio analysis setup failed:", error);
        }
      }

      let audioLevel = 0;

      if (isSpeaking && fakeLip.analyser && fakeLip.dataArray) {
        fakeLip.analyser.getByteTimeDomainData(fakeLip.dataArray);

        let energy = 0;
        for (let index = 0; index < fakeLip.dataArray.length; index += 1) {
          const normalized = (fakeLip.dataArray[index] - 128) / 128;
          energy += normalized * normalized;
        }

        audioLevel = Math.sqrt(energy / fakeLip.dataArray.length);
      }

      const visemeLevel =
        activeViseme.viseme === "viseme_sil" ? 0 : activeViseme.value || 0;
      const targetOpen = isSpeaking
        ? THREE.MathUtils.clamp(Math.max(visemeLevel * 0.7, audioLevel * 3.6), 0, 0.75)
        : 0;
      const speechPulse = isSpeaking
        ? (Math.sin(state.clock.elapsedTime * 14) * 0.5 + 0.5) * targetOpen
        : 0;

      fakeLip.open = THREE.MathUtils.lerp(fakeLip.open, targetOpen, 0.22);

      jawBones.forEach(({ bone, baseRotationX }) => {
        bone.rotation.x = THREE.MathUtils.lerp(
          bone.rotation.x,
          baseRotationX - fakeLip.open * 0.45,
          0.35
        );
      });

      mouthMeshes.forEach(({ mesh, baseScaleY, basePositionY }) => {
        mesh.scale.y = THREE.MathUtils.lerp(
          mesh.scale.y,
          Math.max(0.35, baseScaleY - fakeLip.open * 0.65 - speechPulse * 0.22),
          0.28
        );
        mesh.position.y = THREE.MathUtils.lerp(
          mesh.position.y,
          basePositionY - fakeLip.open * 0.06,
          0.3
        );
      });

      faceMeshes.forEach(
        ({
          mesh,
          baseScaleX,
          baseScaleY,
          baseScaleZ,
          basePositionY,
          baseRotationX,
        }) => {
          const squash = fakeLip.open * 0.06 + speechPulse * 0.02;
          const stretch = fakeLip.open * 0.045 + speechPulse * 0.015;

          mesh.scale.x = THREE.MathUtils.lerp(mesh.scale.x, baseScaleX + stretch, 0.18);
          mesh.scale.y = THREE.MathUtils.lerp(
            mesh.scale.y,
            Math.max(baseScaleY * 0.88, baseScaleY - squash),
            0.18
          );
          mesh.scale.z = THREE.MathUtils.lerp(mesh.scale.z, baseScaleZ + stretch * 0.5, 0.18);
          mesh.position.y = THREE.MathUtils.lerp(
            mesh.position.y,
            basePositionY - fakeLip.open * 0.018,
            0.2
          );
          mesh.rotation.x = THREE.MathUtils.lerp(
            mesh.rotation.x,
            baseRotationX + fakeLip.open * 0.035,
            0.2
          );
        }
      );
    }

    if (avatarRootRef.current) {
      avatarRootRef.current.position.y = Math.sin(state.clock.elapsedTime * 1.35) * 0.015;
      avatarRootRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.35) * 0.04;
      avatarRootRef.current.rotation.x = isSpeaking
        ? Math.sin(state.clock.elapsedTime * 2.2) * 0.018
        : THREE.MathUtils.lerp(avatarRootRef.current.rotation.x, 0, 0.08);
    }
  });

  return <primitive ref={avatarRootRef} object={avatarScene} />;
}

function AvatarCanvas({ children }) {
  return (
    <div className="avatar-viewport">
      <Canvas
        camera={{ position: DEFAULT_CAMERA_POSITION.toArray(), fov: 24 }}
        style={{ width: "100%", height: "100%" }}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
      >
        <color attach="background" args={["#070b12"]} />
        <fog attach="fog" args={["#070b12", 1.8, 4.2]} />

        <ambientLight intensity={0.85} />
        <hemisphereLight intensity={0.8} groundColor="#05070b" color="#d7e7ff" />
        <directionalLight position={[1.8, 2.8, 2.4]} intensity={1.8} color="#fff4df" castShadow />
        <directionalLight position={[-1.5, 1.5, 2]} intensity={0.65} color="#cde1ff" />
        <directionalLight position={[0.2, 1.4, -1.8]} intensity={0.8} color="#00a37a" />
        <spotLight
          position={[0, 2.4, 2.2]}
          angle={0.35}
          penumbra={0.45}
          intensity={0.55}
          color="#ffffff"
        />

        <Environment preset="city" />

        <mesh position={[0, 0, -0.75]} receiveShadow>
          <planeGeometry args={[4.8, 4.8]} />
          <meshStandardMaterial color="#101722" roughness={0.92} metalness={0.02} />
        </mesh>

        <ContactShadows
          position={[0, 0.03, 0]}
          opacity={0.5}
          scale={2.3}
          blur={2.8}
          far={1.8}
        />

        {children}
      </Canvas>
    </div>
  );
}

function GLBAvatarCanvas({ avatarUrl, visemes, isSpeaking, audioRef }) {
  return (
    <AvatarCanvas>
      <Suspense fallback={<LoadingAvatar />}>
        <GLBAvatarModel
          avatarUrl={avatarUrl}
          visemes={visemes}
          isSpeaking={isSpeaking}
          audioRef={audioRef}
        />
      </Suspense>
    </AvatarCanvas>
  );
}

function ProceduralAvatarCanvas({ visemes, isSpeaking, audioRef }) {
  return (
    <AvatarCanvas>
      <ProceduralAvatar
        visemes={visemes}
        isSpeaking={isSpeaking}
        audioRef={audioRef}
      />
    </AvatarCanvas>
  );
}

class AvatarErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidUpdate(prevProps) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.hasError) {
      this.setState({ hasError: false });
    }
  }

  componentDidCatch(error) {
    console.error("Avatar rendering error:", error);
    this.props.onError?.(error);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

export default function Avatar({
  visemes,
  isSpeaking,
  audioRef,
  avatarUrl,
  onAvatarError,
}) {
  const resolvedAvatarUrl = avatarUrl || AVATAR_GLB_URL;
  const proceduralFallback = (
    <ProceduralAvatarCanvas
      visemes={visemes}
      isSpeaking={isSpeaking}
      audioRef={audioRef}
    />
  );

  if (AVATAR_MODE === "procedural" || !resolvedAvatarUrl) {
    return proceduralFallback;
  }

  return (
    <AvatarErrorBoundary
      key={resolvedAvatarUrl}
      resetKey={resolvedAvatarUrl}
      fallback={proceduralFallback}
      onError={onAvatarError}
    >
      <GLBAvatarCanvas
        avatarUrl={resolvedAvatarUrl}
        visemes={visemes}
        isSpeaking={isSpeaking}
        audioRef={audioRef}
      />
    </AvatarErrorBoundary>
  );
}

if (AVATAR_MODE !== "procedural" && AVATAR_GLB_URL) {
  useGLTF.preload(AVATAR_GLB_URL);
}
