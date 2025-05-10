const scalar_ = 100;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 25;
camera.position.x = 4;
camera.position.y = -25;

// Camera Controller
const cameraController = {
    x: camera.position.x,
    y: camera.position.y,
    z: camera.position.z,
};

let controls;
let currentMode = '3D';

function initControls() {
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = false;
    controls.minDistance = 10;
    controls.maxDistance = 100;
    controls.target.set(0, 0, 0);
}

function updateCameraPosition() {
    camera.position.set(
        parseFloat(cameraController.x),
        parseFloat(cameraController.y),
        parseFloat(cameraController.z)
    );
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    needsUpdate = true;
}

// Event Listeners for Camera Control Inputs
const cameraXSlider = document.getElementById('cameraXSlider');
const cameraYSlider = document.getElementById('cameraYSlider');
const cameraZSlider = document.getElementById('cameraZSlider');

cameraXSlider.addEventListener('input', function () {
    cameraController.x = cameraXSlider.value;
    updateCameraPosition();
});

cameraYSlider.addEventListener('input', function () {
    cameraController.y = cameraYSlider.value;
    updateCameraPosition();
});

cameraZSlider.addEventListener('input', function () {
    cameraController.z = cameraZSlider.value;
    updateCameraPosition();
});

const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Montage and Tile Configuration
const montageTilesX = 15;         // Number of tiles horizontally in the montage
const montageTilesY = 15;         // Number of tiles vertically in the montage
const montageTileResolution = 128; // Resolution of each tile (e.g., 128 for 128x128 pixels)

let imagePositions = [];
let spaceBetweenTiles = 0.1;
let needsUpdate = true;
let showAxis = true;
let axesHelper;
let is3D = true;

function loadImage(src) {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.src = src;
        image.onload = () => resolve(image);
        image.onerror = reject;
    });
}

function getChunkedTexture(image, x, y, chunkSize = montageTileResolution) {
    const canvas = document.createElement('canvas');
    canvas.width = chunkSize;
    canvas.height = chunkSize;
    const context = canvas.getContext('2d');
    context.drawImage(image, x, y, chunkSize, chunkSize, 0, 0, chunkSize, chunkSize);
    return new THREE.CanvasTexture(canvas);
}

function createPlane(texture, position) {
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.MeshBasicMaterial({ map: texture });
    const plane = new THREE.Mesh(geometry, material);
    plane.position.set(position.x, position.y, position.z || 0);
    scene.add(plane);
    return plane;
}

function loadVisualizationData() {
    const jsonFile = is3D ? 'atlas_images/images_color_rgb.json' : 'atlas_images/images_color_rgb_2D.json';
    return new Promise((resolve, reject) => {
        new THREE.FileLoader().load(
            jsonFile,
            data => {
                imagePositions = JSON.parse(data);
                resolve();
            },
            undefined,
            reject
        );
    });
}

async function switchVisualizationMode() {
    try {
        currentMode = currentMode === '3D' ? '2D' : '3D';
        
        // Log the state before clearing
        console.log('Before clearing - Scene children:', scene.children.length);
        
        const currentCameraPos = {
            x: camera.position.x,
            y: camera.position.y,
            z: camera.position.z
        };
        
        // Clear existing meshes but keep other objects (like axes)
        const nonMeshObjects = scene.children.filter(child => !(child instanceof THREE.Mesh));
        scene.children = [...nonMeshObjects];
        
        // Log the state after clearing
        console.log('After clearing - Scene children:', scene.children.length);
        
        is3D = currentMode === '3D';
        
        // Load new data
        await loadVisualizationData();
        console.log('Loaded image positions:', imagePositions.length);
        
        await createAndRenderPlanes('./atlas_images/montage_0.png', montageTilesX);
        
        // Log the final state
        console.log('After rendering - Scene children:', scene.children.length);
        
        if (currentMode === '2D') {
            camera.position.set(0, 0, 50);
            controls.minPolarAngle = 0;
            controls.maxPolarAngle = Math.PI / 2;
        } else {
            camera.position.set(currentCameraPos.x, currentCameraPos.y, currentCameraPos.z);
            controls.minPolarAngle = 0;
            controls.maxPolarAngle = Math.PI;
        }
        
        camera.lookAt(0, 0, 0);
        camera.updateProjectionMatrix();
        controls.update();
        
        const button = document.getElementById('toggle2D3DButton');
        if (button) {
            button.textContent = `Switch to ${currentMode === '3D' ? '2D' : '3D'}`;
        }
        
        needsUpdate = true;
    } catch (error) {
        console.error('Error switching visualization mode:', error);
    }
}

async function createAndRenderPlanes(imageSrc, planesPerRow = montageTilesX) {
    const image = await loadImage(imageSrc);
    const chunkSize = montageTileResolution;

    const numImagesInMontage = montageTilesX * montageTilesY;
    const numImagesToRender = Math.min(imagePositions.length, numImagesInMontage);

    for (let i = 0; i < numImagesToRender; i++) {
        const row = Math.floor(i / planesPerRow);
        const col = i % planesPerRow;
        const x = col * chunkSize;
        const y = row * chunkSize;
        
        const texture = getChunkedTexture(image, x, y);
        const position = {
            x: imagePositions[i].x * spaceBetweenTiles,
            y: imagePositions[i].y * spaceBetweenTiles,
            z: is3D ? imagePositions[i].z * spaceBetweenTiles : 0
        };

        createPlane(texture, position);
    }
    needsUpdate = true;
    updateAxesHelper();
}

function updatePlanePositions() {
    scene.children.forEach((child, index) => {
        // Check if child is a mesh AND if imagePositions[index] exists
        if (child instanceof THREE.Mesh && imagePositions[index]) {
            const position = {
                x: imagePositions[index].x * spaceBetweenTiles * scalar_,
                y: imagePositions[index].y * spaceBetweenTiles * scalar_,
                z: is3D ? imagePositions[index].z * spaceBetweenTiles * scalar_ : 0
            };
            child.position.set(position.x, position.y, position.z);
        }
    });
    needsUpdate = true;
}

function updateSpaceBetweenTiles() {
    spaceBetweenTiles = parseFloat(spaceBetweenTilesSlider.value);
    updatePlanePositions();
}

function updateAxesHelper() {
    if (showAxis) {
        if (!axesHelper) {
            axesHelper = new THREE.AxesHelper(5);
            scene.add(axesHelper);
        }
    } else {
        if (axesHelper) {
            scene.remove(axesHelper);
            axesHelper = null;
        }
    }
    needsUpdate = true;
}

function animate() {
    requestAnimationFrame(animate);
    if (controls) {
        controls.update();
    }
    if (needsUpdate || (controls && controls.enabled)) {
        renderer.render(scene, camera);
        needsUpdate = false;
    }
}

// Initial setup
async function init() {
    await loadVisualizationData();
    await createAndRenderPlanes('atlas_images/montage_0.png', montageTilesX);
    initControls();
    animate();
}

// Event listeners
window.addEventListener('resize', function () {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    needsUpdate = true;
});

const zoomSlider = document.getElementById('zoomSlider');
zoomSlider.addEventListener('input', function () {
    const zoomValue = parseFloat(zoomSlider.value);
    camera.zoom = zoomValue;
    camera.updateProjectionMatrix();
    needsUpdate = true;
});

const spaceBetweenTilesSlider = document.getElementById('spaceBetweenTilesSlider');
spaceBetweenTilesSlider.addEventListener('input', updateSpaceBetweenTiles);

const toggleAxesCheckbox = document.getElementById('toggleAxesCheckbox');
toggleAxesCheckbox.addEventListener('change', function () {
    showAxis = toggleAxesCheckbox.checked;
    updateAxesHelper();
});

// Add event listener for 2D/3D toggle button
document.getElementById('toggle2D3DButton').addEventListener('click', switchVisualizationMode);

init();