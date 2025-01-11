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

function updateCameraPosition() {
    camera.position.set(
        parseFloat(cameraController.x),
        parseFloat(cameraController.y),
        parseFloat(cameraController.z)
    );
    camera.lookAt(0, 0, 0); // Ensure the camera points to the center of the scene
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

let imagePositions = [];
let spaceBetweenTiles = 0.1;
let needsUpdate = true;
let showAxis = true; // Variable to control whether axes are displayed
let axesHelper; // To store the axes helper

function loadImage(src) {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.src = src;
        image.onload = () => resolve(image);
        image.onerror = reject;
    });
}

function getChunkedTexture(image, x, y, chunkSize = 128) {
    const canvas = document.createElement('canvas');
    canvas.width = chunkSize;
    canvas.height = chunkSize;
    const context = canvas.getContext('2d');
    context.drawImage(image, x, y, chunkSize, chunkSize, 0, 0, chunkSize, chunkSize);
    return new THREE.CanvasTexture(canvas);
}

function createPlane(texture, positionX, positionY) {
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.MeshBasicMaterial({ map: texture });
    const plane = new THREE.Mesh(geometry, material);
    plane.position.set(positionX, positionY, 0);
    scene.add(plane);
    return plane;
}

let file_loader = new THREE.FileLoader();
file_loader.load('atlas_images/color_coords.json', function(data) {
    imagePositions = JSON.parse(data);
    createAndRenderPlanes('atlas_images/atlas_1.jpg');
});

async function createAndRenderPlanes(imageSrc, planesPerRow = 20) {
    const image = await loadImage(imageSrc);
    const chunkSize = 128;

    for (let i = 0; i < 300; i++) {
        const row = Math.floor(i / planesPerRow);
        const col = i % planesPerRow;
        const x = col * chunkSize;
        const y = row * chunkSize;

        const texture = getChunkedTexture(image, x, y);

        const positionX = imagePositions[i].x * spaceBetweenTiles;
        const positionY = imagePositions[i].y * spaceBetweenTiles;

        createPlane(texture, positionX, positionY);
    }
    needsUpdate = true;
    updateAxesHelper(); // Update axes helper when planes are added
}

function updatePlanePositions() {
    scene.children.forEach((child, index) => {
        if (child instanceof THREE.Mesh) {
            const positionX = imagePositions[index].x * spaceBetweenTiles;
            const positionY = imagePositions[index].y * spaceBetweenTiles;
            child.position.set(positionX, positionY, 0);
        }
    });
    needsUpdate = true;
}

function updateSpaceBetweenTiles() {
    spaceBetweenTiles = parseFloat(spaceBetweenTilesSlider.value);
    updatePlanePositions();
}

// Function to add or remove the axes helper based on showAxis
function updateAxesHelper() {
    if (showAxis) {
        if (!axesHelper) {
            axesHelper = new THREE.AxesHelper(5); // Length of the axes
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
    if (needsUpdate) {
        renderer.render(scene, camera);
        needsUpdate = false;
    }
}
animate();

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

// Toggle axes visibility
const toggleAxesCheckbox = document.getElementById('toggleAxesCheckbox');
toggleAxesCheckbox.addEventListener('change', function () {
    showAxis = toggleAxesCheckbox.checked;
    updateAxesHelper();
});
