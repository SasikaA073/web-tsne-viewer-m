

// Create a scene
const scene = new THREE.Scene();

// Create a camera
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 75;

// Create a renderer
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Declare the imagePositions array to be populated from JSON
let imagePositions = [];
let spaceBetweenTiles = 60;

// Function to load an image
function loadImage(src) {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.src = src;
        image.onload = () => resolve(image);
        image.onerror = reject;
    });
}

// Function to get 128x128px chunks from the image
function getChunkedTexture(image, x, y, chunkSize = 128) {
    // Create a canvas and draw the image chunk
    const canvas = document.createElement('canvas');
    canvas.width = chunkSize;
    canvas.height = chunkSize;
    const context = canvas.getContext('2d');
    context.drawImage(image, x, y, chunkSize, chunkSize, 0, 0, chunkSize, chunkSize);
    
    // Create and return the texture
    return new THREE.CanvasTexture(canvas);
}

// Function to create a plane and apply the texture
function createPlane(texture, positionX, positionY) {
    const geometry = new THREE.PlaneGeometry(2, 2); // Set appropriate size for the plane
    const material = new THREE.MeshBasicMaterial({ map: texture });
    const plane = new THREE.Mesh(geometry, material);
    plane.position.set(positionX, positionY, 0);
    scene.add(plane);
}

// Load the image position JSON file
let file_loader = new THREE.FileLoader();
file_loader.load('atlas_images/coords.json', function(data) {
    imagePositions = JSON.parse(data);
    createAndRenderPlanes('atlas_images/atlas_1.jpg');
});

// Function to create 300 planes and render 128x128px chunks onto them
async function createAndRenderPlanes(imageSrc, planesPerRow = 20) {
    const image = await loadImage(imageSrc);
    const chunkSize = 128;
    
    for (let i = 0; i < 300; i++) {
        const row = Math.floor(i / planesPerRow);
        const col = i % planesPerRow;
        const x = col * chunkSize;
        const y = row * chunkSize;

        // Get the chunk texture from the image
        const texture = getChunkedTexture(image, x, y);

        // Calculate position of each plane from the JSON file
        const positionX = imagePositions[i].x*spaceBetweenTiles; // Assuming the JSON has 'x' and 'y'
        const positionY = imagePositions[i].y*spaceBetweenTiles;

        // Create and render the plane
        createPlane(texture, positionX, positionY);
    }
}

// Render the scene
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

// Resize the renderer when the window is resized
window.addEventListener('resize', function () {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
});

// Add orbit controls
const controls = new THREE.OrbitControls(camera, renderer.domElement);

// Add zoom functionality with a slider
const zoomSlider = document.getElementById('zoomSlider');
zoomSlider.addEventListener('input', function () {
    const zoomValue = parseFloat(zoomSlider.value);
    camera.zoom = zoomValue; // Update camera zoom based on slider value
    camera.updateProjectionMatrix(); // Required after changing zoom
});
