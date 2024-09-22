// Create the scene and a camera to view it
var scene = new THREE.Scene();

/**
* Camera
**/

// Specify the portion of the scene visiable at any time (in degrees)
var fieldOfView = 75;

// Specify the camera's aspect ratio
var aspectRatio = window.innerWidth / window.innerHeight;

// Specify the near and far clipping planes. Only objects
// between those planes will be rendered in the scene
// (these values help control the number of items rendered
// at any given time)
var nearPlane = 0.1;
var farPlane = 1000;

// Use the values specified above to create a camera
var camera = new THREE.PerspectiveCamera(
  fieldOfView, aspectRatio, nearPlane, farPlane
);

// Finally, set the camera's position in the z-dimension
camera.position.z = 5;

/**
* Renderer
**/

// Create the canvas with a renderer
var renderer = new THREE.WebGLRenderer({antialias: true});

// Specify the size of the canvas
renderer.setSize( window.innerWidth, window.innerHeight );

// Add the canvas to the DOM
document.body.appendChild( renderer.domElement );

/**
* Cube
**/

// Create a cube with width, height, and depth set to 1
var geometry = new THREE.BoxGeometry( 1, 1, 1 );

// Use a MeshPhongMaterial to catch the directed light
var material = new THREE.MeshPhongMaterial({ color: 0xffff00 })

// Combine the geometry and material into a mesh
var cube = new THREE.Mesh( geometry, material );

// Add the mesh to our scene
scene.add( cube );

/**
* Lights
**/

// Add a point light with #fff color, .7 intensity, and 0 distance
var light = new THREE.PointLight( 0xffffff, .7, 0 );

// Specify the light's position
light.position.set(1, 1, 100 );

// Add the light to the scene
scene.add(light)

/**
* Render!
**/

// The main animation function that re-renders the scene each animation frame
function animate() {
requestAnimationFrame( animate );
  renderer.render( scene, camera );

  // Rotate the cube a bit each animation frame
  cube.rotation.y += 0.01;
  cube.rotation.z += 0.01;
}
animate();