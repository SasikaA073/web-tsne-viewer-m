// Montage and Tile Configuration
const montageTilesX = 15;         // Number of tiles horizontally in the montage
const montageTilesY = 15;         // Number of tiles vertically in the montage
const montageTileResolution = 256; // Resolution of each tile (e.g., 128 for 128x128 pixels)

const scalar_ = 1;

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

// Loading Progress Variables
let totalAssetsToLoad = 0;
let assetsLoaded = 0;
let loadingOverlay;
let loadingMessage;

let montageFilePaths = [];

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


let imagePositions = [];
let spaceBetweenTiles = 0.1;
let needsUpdate = true;
let showAxis = true;
let axesHelper;
let is3D = true;

function updateLoadingProgress() {
    assetsLoaded++;
    const percentage = totalAssetsToLoad > 0 ? Math.round((assetsLoaded / totalAssetsToLoad) * 100) : 0;
    if (loadingMessage) {
        loadingMessage.textContent = `Loading ${percentage}%`;
    }
    if (assetsLoaded >= totalAssetsToLoad && loadingOverlay) {
        // Ensure this runs after a very short delay to allow the final message to render if needed.
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
        }, 50); // Small delay
    }
}

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
    let jsonFile;
    // Determine the JSON file based on the current mode
    if (currentMode === '3D') {
        jsonFile = 'atlas_images/images_color_rgb.json';
    } else if (currentMode === '2D_GRID') { // Assumes '2D_GRID' as a new mode value
        jsonFile = 'atlas_images/images_color_rgb_2D_grid.json';
    } else { // Default to original 2D mode (e.g., currentMode === '2D')
        jsonFile = 'atlas_images/images_color_rgb_2D.json';
    }

    return new Promise((resolve, reject) => {
        new THREE.FileLoader().load(
            jsonFile,
            data => {
                imagePositions = JSON.parse(data);
                updateLoadingProgress(); // Update progress for the loaded JSON file
                resolve();
            },
            undefined,
            (error) => {
                console.error("Error loading JSON data:", error);
                updateLoadingProgress(); // Still update progress even on error to not hang the bar
                reject(error);
            }
        );
    });
}

// Add this async function to discover montage files
async function discoverMontageFiles() {
    const maxAttempts = 20; // Maximum number of montage files to check for
    const discoveredFiles = [];
    
    for (let i = 0; i < maxAttempts; i++) {
        const path = `./atlas_images/montage_${i}.jpg`;
        try {
            // Attempt to load the image
            await loadImage(path);
            discoveredFiles.push(path);
        } catch (error) {
            // Stop searching if we get 2 consecutive errors (in case of temporary network issues)
            if (i > 0 && !discoveredFiles.length) break;
            if (i > discoveredFiles.length + 2) break;
        }
    }
    return discoveredFiles;
}

async function switchVisualizationMode() {
    try {
        // Rediscover montage files on each mode switch
        montageFilePaths = await discoverMontageFiles();
        console.log('Found montage files:', montageFilePaths);
        
        if (loadingOverlay) loadingOverlay.style.display = 'flex';
        assetsLoaded = 0;
        totalAssetsToLoad = 1 + montageFilePaths.length;
        if (loadingMessage) loadingMessage.textContent = 'Loading 0%';

        // Determine the new currentMode based on the existing currentMode
        let newCurrentModeValue;
        if (currentMode === '3D') {
            newCurrentModeValue = '2D';
        } else if (currentMode === '2D') {
            newCurrentModeValue = '2D_GRID';
        } else { // currentMode was '2D_GRID' (or an unexpected state, defaulting to 3D)
            newCurrentModeValue = '3D';
        }
        currentMode = newCurrentModeValue; // Update global currentMode
        
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
        
        is3D = currentMode === '3D'; // Update global is3D based on the *new* currentMode
        
        // Load new data
        await loadVisualizationData(); // This uses the updated currentMode
        console.log('Loaded image positions:', imagePositions.length);
        
        let accumulatedImageOffset = 0;
        for (const filePath of montageFilePaths) {
            // createAndRenderPlanes will call updateLoadingProgress for each montage
            const renderedCount = await createAndRenderPlanes(filePath, montageTilesX, accumulatedImageOffset);
            accumulatedImageOffset += renderedCount;
        }
        
        // Log the final state
        console.log('After rendering - Scene children:', scene.children.length);
        
        // Update camera and controls based on the new currentMode
        if (currentMode === '3D') {
            camera.position.set(currentCameraPos.x, currentCameraPos.y, currentCameraPos.z);
            controls.minPolarAngle = 0;
            controls.maxPolarAngle = Math.PI;
        } else { // Covers '2D' and '2D_GRID' modes
            camera.position.set(0, 0, 50);
            controls.minPolarAngle = 0; 
            controls.maxPolarAngle = Math.PI / 2; // Using original 2D settings
        }
        
        camera.lookAt(0, 0, 0);
        camera.updateProjectionMatrix();
        controls.update();
        
        const button = document.getElementById('toggle2D3DButton');
        if (button) {
            // Determine button text based on the *new* currentMode, showing the *next* mode on click
            let buttonTextNextModeDisplay;
            if (currentMode === '3D') {
                buttonTextNextModeDisplay = '2D';
            } else if (currentMode === '2D') {
                buttonTextNextModeDisplay = '2D Grid'; // User-friendly name for the button
            } else { // currentMode is '2D_GRID'
                buttonTextNextModeDisplay = '3D';
            }
            button.textContent = `Switch to ${buttonTextNextModeDisplay}`;
        }
        
        needsUpdate = true;
    } catch (error) {
        console.error('Error switching visualization mode:', error);
        if (loadingOverlay) loadingOverlay.style.display = 'none'; // Hide on error
    }
}

async function createAndRenderPlanes(imageSrc, planesPerRow = montageTilesX, imagePositionOffset = 0) {
    let image;
    try {
        image = await loadImage(imageSrc);
        updateLoadingProgress(); // Montage image file is loaded or load attempt finished
    } catch (error) {
        console.error(`Error loading image ${imageSrc}:`, error);
        updateLoadingProgress(); // Still count as an "attempted" asset load for progress
        return 0; // Failed to load image, render nothing from it
    }
    
    const chunkSize = montageTileResolution;

    const maxTilesInThisMontageFile = planesPerRow * montageTilesY;
    // Number of images to render from this montage, constrained by available positions and what's in the montage file
    const imagesToProcessForThisMontage = Math.min(imagePositions.length - imagePositionOffset, maxTilesInThisMontageFile);

    if (imagesToProcessForThisMontage <= 0) {
        console.warn(`No images to process for ${imageSrc} with offset ${imagePositionOffset} or imagePositions exhausted.`);
        return 0; // No images rendered from this montage
    }

    for (let i = 0; i < imagesToProcessForThisMontage; i++) {
        const dataIndex = imagePositionOffset + i;
        // Safety check, though Math.min should prevent this for imagePositions.length
        if (dataIndex >= imagePositions.length) {
            console.warn(`Attempted to access imagePosition out of bounds: ${dataIndex} while processing ${imageSrc}.`);
            break;
        }
        
        const row = Math.floor(i / planesPerRow);
        const col = i % planesPerRow;
        const x = col * chunkSize;
        const y = row * chunkSize;
        
        const texture = getChunkedTexture(image, x, y);

        let effectiveSpaceMultiplier;
        if (currentMode === '2D_GRID') {
            // For 2D_GRID: tile width is 2, no gap. Center-to-center = 2.0.
            effectiveSpaceMultiplier = 2.0;
        } else {
            effectiveSpaceMultiplier = spaceBetweenTiles;
        }

        const position = {
            x: imagePositions[dataIndex].x * effectiveSpaceMultiplier,
            y: imagePositions[dataIndex].y * effectiveSpaceMultiplier,
            // Z position is 0 for 2D/2D_GRID, or calculated for 3D
            z: (currentMode === '3D') ? imagePositions[dataIndex].z * effectiveSpaceMultiplier : 0
        };

        createPlane(texture, position);
    }
    needsUpdate = true;
    updateAxesHelper();
    return imagesToProcessForThisMontage; // Return how many images were actually processed/rendered from imagePositions
}

function updatePlanePositions() {
    scene.children.forEach((child, index) => {
        // Check if child is a mesh AND if imagePositions[index] exists
        if (child instanceof THREE.Mesh && imagePositions[index]) {
            let effectiveSpaceMultiplier;
            if (currentMode === '2D_GRID') {
                // For 2D_GRID: tile width is 2, no gap. Center-to-center = 2.0.
                effectiveSpaceMultiplier = 2.0;
            } else {
                effectiveSpaceMultiplier = spaceBetweenTiles;
            }

            const position = {
                x: imagePositions[index].x * effectiveSpaceMultiplier * scalar_,
                y: imagePositions[index].y * effectiveSpaceMultiplier * scalar_,
                // Z position is 0 for 2D/2D_GRID, or calculated for 3D
                z: (currentMode === '3D') ? imagePositions[index].z * effectiveSpaceMultiplier * scalar_ : 0
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
    // Discover montage files first
    montageFilePaths = await discoverMontageFiles();
    console.log('Found montage files:', montageFilePaths);

    // Get references to loading elements
    loadingOverlay = document.getElementById('loading-overlay');
    loadingMessage = document.getElementById('loading-message');

    // Initialize progress
    assetsLoaded = 0;
    // Total assets: 1 JSON + number of montage files
    totalAssetsToLoad = 1 + montageFilePaths.length;

    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex'; // Show loading screen
    }
    if (loadingMessage) {
        loadingMessage.textContent = 'Loading 0%';
    }

    try {
        await loadVisualizationData(); // This will call updateLoadingProgress for the JSON

        let accumulatedImageOffset = 0;
        for (const filePath of montageFilePaths) {
            // createAndRenderPlanes will call updateLoadingProgress for each montage
            const renderedCount = await createAndRenderPlanes(filePath, montageTilesX, accumulatedImageOffset);
            accumulatedImageOffset += renderedCount;
        }
    } catch (error) {
        console.error("Error during initial asset loading:", error);
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none'; // Hide loading bar on critical error
        }
        // Optionally, display an error message to the user here
        return; // Stop further initialization
    }
    
    // All assets should be loaded by now, and updateLoadingProgress should have hidden the overlay
    // if assetsLoaded >= totalAssetsToLoad.

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