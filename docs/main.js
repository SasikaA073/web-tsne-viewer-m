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

async function switchVisualizationMode(newMode) {
    try {
        // Rediscover montage files on each mode switch
        montageFilePaths = await discoverMontageFiles();
        console.log('Found montage files:', montageFilePaths);
        
        if (loadingOverlay) loadingOverlay.style.display = 'flex';
        assetsLoaded = 0;
        totalAssetsToLoad = 1 + montageFilePaths.length;
        if (loadingMessage) loadingMessage.textContent = 'Loading 0%';

        currentMode = newMode; // Update to new mode directly
        
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
        
        let accumulatedImageOffset = 0;
        for (const filePath of montageFilePaths) {
            const renderedCount = await createAndRenderPlanes(filePath, montageTilesX, accumulatedImageOffset);
            accumulatedImageOffset += renderedCount;
        }
        
        // Log the final state
        console.log('After rendering - Scene children:', scene.children.length);
        
        if (currentMode === '3D') {
            camera.position.set(currentCameraPos.x, currentCameraPos.y, currentCameraPos.z);
            controls.minPolarAngle = 0;
            controls.maxPolarAngle = Math.PI;
        } else {
            camera.position.set(0, 0, 50);
            controls.minPolarAngle = 0;
            controls.maxPolarAngle = Math.PI / 2;
        }
        
        camera.lookAt(0, 0, 0);
        camera.updateProjectionMatrix();
        controls.update();
        
    } catch (error) {
        console.error('Error switching visualization mode:', error);
        if (loadingOverlay) loadingOverlay.style.display = 'none';
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

// Create and add the mode selector with radio buttons
function createModeSelector() {
    const sliderContainer = document.querySelector('.slider-container');
    if (!sliderContainer) {
        console.error('.slider-container not found. Cannot add mode selector.');
        return;
    }

    // Create the main div for this control, styled like other sliders
    const modeControlDiv = document.createElement('div');
    modeControlDiv.classList.add('slider');
    // Dark theme styling
    modeControlDiv.style.backgroundColor = 'rgba(40, 40, 40, 0.7)';
    modeControlDiv.style.border = '1px solid rgba(70, 70, 70, 0.5)';
    modeControlDiv.style.borderRadius = '5px';
    modeControlDiv.style.padding = '15px';
    modeControlDiv.style.marginTop = '15px';
    modeControlDiv.style.marginBottom = '15px';
    modeControlDiv.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.2)';
    modeControlDiv.style.color = 'white';
    // Change to vertical layout
    modeControlDiv.style.display = 'flex';
    modeControlDiv.style.flexDirection = 'column';

    // 1. Title Span
    const titleSpan = document.createElement('span');
    titleSpan.textContent = 'Visualization Mode:';
    titleSpan.style.marginBottom = '15px';
    titleSpan.style.fontWeight = 'bold';
    titleSpan.style.color = 'white';
    titleSpan.style.fontSize = '16px';
    modeControlDiv.appendChild(titleSpan);

    // 2. Radio Buttons Group - now vertical
    const radioGroup = document.createElement('div');
    radioGroup.style.display = 'flex';
    radioGroup.style.flexDirection = 'column';
    radioGroup.style.gap = '10px'; // Space between vertical options
    
    const modes = [
        { value: '3D', label: '3D View' },
        { value: '2D', label: '2D View' },
        { value: '2D_GRID', label: 'Grid View' }
    ];

    modes.forEach(modeInfo => {
        // Create a container for each option
        const optionContainer = document.createElement('div');
        optionContainer.style.backgroundColor = 'rgba(30, 30, 30, 0.7)';
        optionContainer.style.borderRadius = '4px';
        optionContainer.style.padding = '2px';
        optionContainer.style.transition = 'all 0.2s';
        
        // Create the radio label inside the container
        const radioLabel = document.createElement('label');
        radioLabel.style.cursor = 'pointer';
        radioLabel.style.display = 'flex';
        radioLabel.style.alignItems = 'center';
        radioLabel.style.padding = '10px 15px';
        radioLabel.style.width = '100%';
        radioLabel.style.color = 'white';
        radioLabel.style.boxSizing = 'border-box';
        
        // Radio input
        const radioInput = document.createElement('input');
        radioInput.type = 'radio';
        radioInput.name = 'visualizationMode';
        radioInput.id = `mode-radio-${modeInfo.value}`;
        radioInput.value = modeInfo.value;
        radioInput.checked = currentMode === modeInfo.value;
        radioInput.style.marginRight = '12px';
        radioInput.style.cursor = 'pointer';
        radioInput.style.accentColor = '#4285f4'; // Blue accent color for selected radio

        // Text span
        const textSpan = document.createElement('span');
        textSpan.textContent = modeInfo.label;
        textSpan.style.flex = '1';
        
        // Highlight the selected mode's container
        if (radioInput.checked) {
            optionContainer.style.backgroundColor = 'rgba(66, 133, 244, 0.3)';
            optionContainer.style.boxShadow = '0 0 0 1px rgba(66, 133, 244, 0.5)';
            textSpan.style.fontWeight = 'bold';
        }

        // Hover effects - applied to the container
        optionContainer.addEventListener('mouseenter', () => {
            if (!document.getElementById(`mode-radio-${modeInfo.value}`).checked) {
                optionContainer.style.backgroundColor = 'rgba(80, 80, 80, 0.5)';
            } else {
                // Even on the selected item, give some hover feedback
                optionContainer.style.backgroundColor = 'rgba(66, 133, 244, 0.4)';
            }
        });
        
        optionContainer.addEventListener('mouseleave', () => {
            if (!document.getElementById(`mode-radio-${modeInfo.value}`).checked) {
                optionContainer.style.backgroundColor = 'rgba(30, 30, 30, 0.7)';
            } else {
                optionContainer.style.backgroundColor = 'rgba(66, 133, 244, 0.3)';
            }
        });

        // Change event
        radioInput.addEventListener('change', () => {
            if (radioInput.checked) {
                // Update all containers when selection changes
                document.querySelectorAll('[name="visualizationMode"]').forEach(input => {
                    const label = input.parentElement;
                    const container = label.parentElement;
                    const textElement = label.querySelector('span');
                    
                    if (input.checked) {
                        container.style.backgroundColor = 'rgba(66, 133, 244, 0.3)';
                        container.style.boxShadow = '0 0 0 1px rgba(66, 133, 244, 0.5)';
                        textElement.style.fontWeight = 'bold';
                    } else {
                        container.style.backgroundColor = 'rgba(30, 30, 30, 0.7)';
                        container.style.boxShadow = 'none';
                        textElement.style.fontWeight = 'normal';
                    }
                });
                
                switchVisualizationMode(modeInfo.value);
            }
        });

        // Assemble the label
        radioLabel.appendChild(radioInput);
        radioLabel.appendChild(textSpan);
        
        // Put the label in the container
        optionContainer.appendChild(radioLabel);
        
        // Add the option container to the radio group
        radioGroup.appendChild(optionContainer);
    });
    
    modeControlDiv.appendChild(radioGroup);

    // Insert the new mode control div into the sliderContainer, after the H2 element
    const h2Element = sliderContainer.querySelector('h2');
    if (h2Element && h2Element.nextSibling) {
        sliderContainer.insertBefore(modeControlDiv, h2Element.nextSibling);
    } else if (h2Element) {
        sliderContainer.appendChild(modeControlDiv);
    } else {
        sliderContainer.prepend(modeControlDiv);
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
    totalAssetsToLoad = 1 + montageFilePaths.length;

    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
    if (loadingMessage) {
        loadingMessage.textContent = 'Loading 0%';
    }

    try {
        await loadVisualizationData();

        let accumulatedImageOffset = 0;
        for (const filePath of montageFilePaths) {
            const renderedCount = await createAndRenderPlanes(filePath, montageTilesX, accumulatedImageOffset);
            accumulatedImageOffset += renderedCount;
        }
    } catch (error) {
        console.error("Error during initial asset loading:", error);
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        return;
    }

    initControls();
    createModeSelector(); // Add mode selector
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

init();