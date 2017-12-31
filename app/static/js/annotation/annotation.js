var canvas_width = 0;
var canvas_height = 0;

var canvas_start_x = 0;
var canvas_start_y = 0;
var editing = false;
var building_box = false;
var found_box = false;
var resizing = false;

var boxes = [];
var edit_colour = null;   // TODO



function getRandomInt(min, max) {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min)) + min; 
}

class box {
	constructor () {
		this.id = getRandomInt(0, 99999),
		this.x_min = null,
		this.y_min = null,
		this.x_max = null,
		this.y_max = null,
		this.width = null,
		this.height = null,
		this.label = new label_,
        this.image_id = null,
		this.colour = 'blue'
	}
}

class image_ {
    constructor() {
        this.id = getRandomInt(0, 99999),  //gets replaced from db
        this.public_url = null,
        this.width = null,
        this.height = null,
        this.public_url_thumb = null,
        this.is_test_image = null,
        this.original_filename = null
    }
}

class info_ {
	constructor () {
		self.current_box_id = 0,
		self.status = 1
	}
}

class label_ {
    constructor() {
        self.id = null,
        self.name = null,
        self.colour = "blue",
        self.is_active = false
    }
}

class version_ {
    constructor() {
        self.id = null,
        self.train_length = null
    }
}

class user_ {
    constructor() {
        self.id = null,
        self.email = null
    }
}

var info = new info_;
var target = new box;
var Images = [];
var current_image = new image_;
var Labels = [];
var new_label = new label_;
var version = new version_;
var new_user = new user_

var user_vue = new Vue({
    el: "#userbase",
    created: function () {
        Vue.prototype.$http = axios;
        this.get_user();
        user_vue_context = this
    },
    data: {
        user_email: new_user.email
    },
    methods: {
        get_user: function () {

            this.$http.get('/user/view', {
            })
            .then(function (response) {
                user_vue_context.user_email = response.data.user.user['email']
            })
            .catch(function (error) {
                console.log(error);
            });

        }
    }
})

var version_vue = new Vue({
    el: "#version_id",
    created: function () {
        Vue.prototype.$http = axios;
        this.get_version();
    },
    data: {
        train_length: null,
        test_length: null
    },
    methods: {

        get_version: function () {

            that = this
          
            this.$http.get('/version/current/json', {
            })
            .then(function (response) {

            console.log(response)
            that.train_length = response.data.version.version['train_length']
            that.test_length = response.data.version.version['test_length']
            //console.log()

            })

            .catch(function (error) {
            console.log(error);
            });
        }
    }
})


var label_vue = new Vue({
    el: "#labels",
    mounted: function (event) {

        Vue.prototype.$http = axios;
        this.refresh_labels_function()
    },
    created: function () {
    },
    destroyed: function () {
    },

    data: {
        Labels: Labels,
        new_label: new_label
    },

    methods: {
        new_label_function: function () {

            console.log("New label")
            this.$http.post('/labels/new', {
                label: new_label
            })
            .then(function (response) {
                new_label.error = response.data['error'];
            })
            .catch(function (error) {
                console.log(error);
            });  

            this.refresh_labels_function()

        },

        refresh_labels_function: function () {

            console.log("Refreshing labels ids");
            Labels.splice(0, Labels.length)

            this.$http.get('/labels/json', {
            })
            .then(function (response) {

                //console.log(response)

                for (j in response.data.ids) {
                    var label = new label_;

                    label.id = response.data.ids[j];
                    label.name = response.data.names[j];

                    this.Labels.push(label);
                }

                this.Labels[0].is_active = true;

            })
            .catch(function (error) {
                console.log(error);
            });

        },
        change_label_function: function (label) {

            console.log("Changing active label (not fully implemented fully)");

            // better way to do this....
            for (i in Labels) {
                if (Labels[i].id == label.id) {
                    Labels[i].is_active = true;
                } else {
                    Labels[i].is_active = false;
                }
            }
            Labels.splice(Labels.length) // see https://vuejs.org/v2/guide/list.html#Replacing-an-Array
        },
        delete_label_function: function (label) {

            console.log("Deleting label");

            this.$http.post('/labels/delete', {
                label: label
            })
            .then(function (response) {

                console.log(response)

            })
            .catch(function (error) {
                console.log(error);
            });

            // Doing this server side overkill???
            // TODO using soft delete so add undo action
            this.refresh_labels_function();
        }
    }

})


var images_vue = new Vue({
    el: "#images",
    mounted: function (event) {
     
    },
    created: function () { 

        Vue.prototype.$http = axios
        // Images

        this.get_images()

        // TODO better way....
    },
    destroyed: function () {     
    },

    data: {
        Images: Images,
        current_image: current_image,
        Loading: "Loading",
        search_term: null,
    },

    methods: {
        change_image: function (image, use_index, direction) {
            console.log("Changing image")

            // causing strange issues
            // annotate.save()

            // for arrow keys
            if (use_index == true) {
                i = Images.findIndex(x => x.id == current_image.id)
                if (direction == 1) {
                    i += 1
                } else {
                    i -= 1
                }

                // limits
                if (i < 0) { i = 0 }
                if (i >= Images.length ) { i = Images.length - 1 }

                image = Images[i]
            }

            // TODO switch to shallow copy ie jquery
            // TODO look at computed properties closer
            current_image.id = image.id,
            current_image.original_filename = image.original_filename,
            current_image.width = image.width,
            current_image.height = image.height,
            current_image.public_url = image.public_url
            current_image.is_test_image = image.is_test_image
            
            annotate.get_boxes()


        },
        get_images: function (event) {
            console.log("Getting images")

            Images.splice(0, Images.length)  // Reset

            this.$http.post('/images/get', {

                search_term: this.search_term

            })
                .then(function (response) {

                    console.log(response)

                    for (i in response.data.images) {
                        var image = new image_;
                        image.id = response.data.images[i]['image']['id'];
                        image.width = response.data.images[i]['image']['width'];
                        image.height = response.data.images[i]['image']['height'];
                        image.public_url = response.data.images[i]['image']['url_signed'];
                        image.public_url_thumb = response.data.images[i]['image']['url_signed_thumb'];
                        image.is_test_image = response.data.images[i]['image']['is_test_image'];
                        image.original_filename = response.data.images[i]['image']['original_filename'];
                        image.done_labeling = response.data.images[i]['image']['done_labeling'];
                        Images.push(image)
                    }
                    current_image.id = Images[0].id,
                    current_image.width = Images[0].width,
                    current_image.height = Images[0].height,
                    current_image.public_url = Images[0].public_url,
                    current_image.is_test_image = Images[0].is_test_image,
                    current_image.original_filename = Images[0].original_filename


                })
                .catch(function (error) {
                    console.log(error);
                });

            this.Loading = "";


        }
    }

})

var annotate = new Vue({
	el: "#annotate",
    mounted: function (event) {
        // needs to be here as gets by element
		this.c = document.getElementById("annotate_canvas"),
		this.ctx = this.c.getContext("2d") 


	},
	created: function () {
        Vue.prototype.$http = axios;
        window.addEventListener('keyup', this.toggle_edit);
    },
	destroyed: function() {
		window.removeEventListener('keyup')
	},

	data: {
        box: box,
        boxes: boxes,
		info: info,
		target: target,
        editing: editing,
        current_image: images_vue.current_image
    },

	methods: {
        mouse_down: function (event) {
			// - this.canvas_rectangle is to allow for canvas being offset from 0,0 origin
            target.x_min = event.clientX - this.canvas_rect_left,
            target.y_min = event.clientY - this.canvas_rect_top
            
			// detect if on existing box.
			if (editing == true) {
				// find nearest box
				for (i in boxes) {
					b = boxes[i];
					if (target.x_min > b.x_min && target.x_min < b.x_max
						&& target.y_min > b.y_min && target.y_min < b.y_max) {
						
						console.log("Found box", b.id)
						found_box = true;
						this.box = b;
						info.current_box_id = b.id;
						this.box.colour = 'red';
					}
				}
			}
			else {
				building_box = true,
				//console.log("new ", box_.id),
                this.box = new box,
                this.box.image_id = images_vue.current_image.id

                // Labels
                // TODO better way... maybe cache active label or something
                for (i in label_vue.Labels) {
                    if (label_vue.Labels[i].is_active == true) {
                        this.box.label = $.extend({}, label_vue.Labels[i]) 
                    }
                }
				//console.log("this.", this.box.id),
			}
		},
		draw_target_reticle: function(event) {
			
			this.ctx.beginPath(),
			this.ctx.lineWidth = '2',
			this.ctx.strokeStyle = 'green',

			this.ctx.setLineDash([10, 5]),
			this.ctx.moveTo(target.x_max-5, target.y_max), // line x, y start
			this.ctx.lineTo(0, target.y_max),  // x coordinate line to, y line to (end)
			
			this.ctx.moveTo(target.x_max+5, target.y_max), // line x, y start
			this.ctx.lineTo(800, target.y_max),

			this.ctx.moveTo(target.x_max, target.y_max-5), // line x, y start
			this.ctx.lineTo(target.x_max, 0),  // x coordinate line to, y line to (end)
			
			this.ctx.moveTo(target.x_max, target.y_max+5), // line x, y start
			this.ctx.lineTo(target.x_max, 800),

			this.ctx.stroke()
		},

		draw_shared: function(event) {
			this.ctx.beginPath(),
			this.ctx.setLineDash([0]),
			this.ctx.lineWidth = '2'
		},
		
		draw_box: function(event) {

			this.draw_shared();
			this.ctx.strokeStyle = this.box.colour,
			this.ctx.rect(this.box.x_min, this.box.y_min, this.box.width, this.box.height),
			this.ctx.stroke()

		},
		draw_box_b: function(event) {

			//console.log(b.id)
			this.draw_shared();
			this.ctx.strokeStyle = b.colour,
			this.ctx.rect(b.x_min, b.y_min, b.width, b.height),
			this.ctx.stroke()

        },

        draw_canvas: function () {
            // reset canvas and draw existing boxes
            this.img = document.getElementById("a");
            this.ctx.clearRect(canvas_start_x, canvas_start_y, canvas_width, canvas_height);
            this.ctx.drawImage(this.img, canvas_start_x, canvas_start_y);
        },
		mouse_move: function(event) {

            this.draw_canvas(),
			
			// update where canvas is
			this.canvas_rect = this.c.getBoundingClientRect(),
			this.canvas_rect_left = this.canvas_rect.left,  // x offset
			this.canvas_rect_top = this.canvas_rect.top // y offset

            if (typeof event !== 'undefined') {
                target.x_max = event.clientX - this.canvas_rect_left;
                target.y_max = event.clientY - this.canvas_rect_top;
            }
			//console.log(this.canvas_rect_top);
			////// WIP
			if (building_box == true) {

				this.box.x_max = target.x_max,
				this.box.y_max = target.y_max,
				this.box.x_min = target.x_min,
				this.box.y_min = target.y_min,
				this.box.width = target.x_max - target.x_min,
				this.box.height = target.y_max - target.y_min;

			}
			// TODO better way to do this
			// TODO better convention for target x min/ x_max should be one x
			if (editing == true) {

				for (i in boxes) {
					b = boxes[i];
					if (target.x_max > b.x_min && target.x_max < b.x_max
						&& target.y_max > b.y_min && target.y_max < b.y_max) {

						$('#annotate_canvas').css('cursor', 'pointer');
					} else {
						$('#annotate_canvas').css('cursor', 'default');
					}
				}
			}

			if (found_box == true) {

				$('#annotate_canvas').css('cursor', 'pointer');

				if (resizing == true) { 

					this.box.width += event.movementX; 
					this.box.height += event.movementY;

				} 
				if (editing == true ) {
					this.box.x_max += event.movementX ,
					this.box.y_max += event.movementY ,
					this.box.x_min += event.movementX ,
					this.box.y_min += event.movementY
				}

			}

			this.render_boxes();
		},

		render_boxes: function(event){
			
			for (i in boxes) { // Reset box colours
				   boxes[i].colour = 'blue';
			}

			if (info.current_box_id > 0){  // colour selected box
				if (this.box.id == info.current_box_id) {
					this.box.colour = 'red';
				}
			}

			// refactor "edit" to be more generic concept
			if (resizing == false && editing == false) {
		
				this.draw_target_reticle()
			}


			if (building_box == true) {
				this.draw_box(this.box)
			}

			if (boxes.length > 0) {
				for (i in boxes) {

					b = boxes[i],
					this.draw_box_b(b.x_min, b.y_min, b.width, b.height, b.colour)
				}
			}

		},

		mouse_up: function(event) {
			if (building_box == true) {
				boxes.push(this.box);
				building_box = false;
			}
			if (editing == true) {  // reset 
				found_box = false;
			}

		},

        // rename something better
		toggle_edit: function(event) {
			
			if (event.keyCode === 27){
				this.toggle_edit_button();
			}
			/* Disabled resize it's buggy
			if (event.keyCode === 82) {  // r
				this.toggle_resize_button();
			}
			*/
            if (event.keyCode === 83) { // save
                this.save();
            }
			if (event.keyCode === 46) {  // delete
				this.delete_button();
            }
            if (event.keyCode === 37) { // left arrow
                images_vue.change_image(image = null, use_index=true, direction=0);
            }
            if (event.keyCode === 39) { // right arrow
                images_vue.change_image(image = null, use_index = true, direction =1);
            }
		}, // Refactor to generic call edit function

		toggle_edit_button: function(event) {
		
			console.log("Toggled editing");
			editing ^= true;
			this.editing = editing;   // TODO refactor, this is for view
			found_box = false;
			if (editing == false) {
				$('#annotate_canvas').css('cursor', 'default');
			}
		},

		delete_button: function(event) {
		
			console.log("Deleted", info.current_box_id);
			info.status = "Deleted box"+info.current_box_id;
			this.info = info;

			for (i in boxes) {
				if (boxes[i].id == info.current_box_id ) {
					boxes.splice(i, 1)
				}
			}
			this.render_boxes();  // refresh
		},

		toggle_resize_button: function(event) {
		
		 // r
			console.log("Resizing");
			resizing ^= true;
			if (resizing == true) {
				$('#annotate_canvas').css('cursor', 'e-resize');
			} else {
				$('#annotate_canvas').css('cursor', 'default');
			}
		
		},

		save: function(event) {

            console.log("Saving")

            this.$http.post('/annotation/boxes/update', {
                boxes: boxes,
                image_id: images_vue.current_image.id
			})
			.then(function (response) {
			console.log(response);
			})
			.catch(function (error) {
			console.log(error);
			});
        },

        build_yaml: function (event) {

            console.log("Building YAML")

            this.$http.post('/yaml/new', {
            })
            .then(function (response) {
                console.log(response);
            })
            .catch(function (error) {
                console.log(error);
            });
        },

        build_tfrecords: function (event) {

            console.log("Building tfrecords")

            this.$http.post('/tfrecords/new', {
            })
            .then(function (response) {
                console.log(response);
            })
            .catch(function (error) {
                console.log(error);
            });
        },
        get_boxes: function () {
            // Boxes
            console.log("Getting boxes")
            this.$http.post('/boxes/get/json', {

                image_id: images_vue.current_image.id

            })
            .then(function (response) {

                this.boxes.splice(0, boxes.length)  // Reset

                new_boxes = response.data.boxes
                new_labels = response.data.labels
                for (i in new_boxes) {

                    _box = new box;
                    // surely better way to do this
                    // best way to copy all matching properties?
                    //_box = $.extend({}, new_boxes[i]);
                    //_box = JSON.parse(JSON.stringify(new_boxes[i]));

                    _box.id = new_boxes[i]['box']['id'];
                    _box.x_min = new_boxes[i]['box']['x_min'];
                    _box.y_min = new_boxes[i]['box']['y_min'];
                    _box.x_max = new_boxes[i]['box']['x_max'];
                    _box.y_max = new_boxes[i]['box']['y_max'];
                    _box.width = new_boxes[i]['box']['width'];
                    _box.height = new_boxes[i]['box']['height'];
                    _box.image_id = new_boxes[i]['box']['image_id'];

                    _box.label.id = new_labels[i]['label']['id'];
                    _box.label.name = new_labels[i]['label']['name'];
                    
                    //console.log(_box.label.name);

                    this.boxes.push(_box);
                }

                annotate.draw_canvas();
                annotate.render_boxes();

                setTimeout(function () {
                    annotate.mouse_move()
                }, 500);

                setTimeout(function () {
                    annotate.mouse_move()
                }, 1000);

                setTimeout(function () {
                    annotate.mouse_move()
                }, 2000);

                //console.log(boxes)
                
                
            })
            .catch(function (error) {
                console.log(error);
                });

        },
        run_training: function () {
            console.log("Starting training")
            this.$http.get('/machine_learning/training/run', {
           
            })
            .then(function (response) {

                alert(response.data['train_credits'])
                console.log(response);

            })
            .catch(function (error) {
                console.log(error);
            });

        },
        run_frozen: function () {
            console.log("Starting freeze")
            this.$http.get('/machine_learning/training/frozen/run', {
     
            })
            .then(function (response) {

                console.log(response);

            })
            .catch(function (error) {
                console.log(error);
            });

        },
        run_new_model: function () {
            console.log("Creating new model")
            this.$http.post('/machine_learning/training/new_model', {
   
            })
                .then(function (response) {

                    console.log(response);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        run_new_version: function () {
            console.log("Creating new version")
            this.$http.get('/machine_learning/training/new_version', {

            })
            .then(function (response) {

                console.log(response);

            })
            .catch(function (error) {
                console.log(error);
            });

        },
        runSingleInference: function () {

            console.log("Running inference")
            this.$http.get('/machine_learning/inference/run', {
 
            })
                .then(function (response) {

                    console.log(response);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        runTrainingPipeline: function () {

            console.log("Running training pipeline")
            this.$http.get('/machine_learning/training/run/all/0', {
  
            })
                .then(function (response) {

                    console.log(response);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        runBatchInference: function () {

            console.log("Running runBatchInference")
            this.$http.post('/machine_learning/inference/batch/run', {

            })
                .then(function (response) {

                    console.log(response);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        buildLabelMap: function () {

            console.log("Build label map")
            this.$http.get('/labels/machine_learning/label_map/new', {

            })
                .then(function (response) {

                    console.log(response);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        toggleTestImage: function (image) {

            console.log("toggleTestImage")
            this.$http.post('/images/edit/toggle_test_image', {

                image: image
            })
                .then(function (response) {

                    console.log(response);
                    location.reload();

                })
                .catch(function (error) {
                    console.log(error);
                });

            // TODO use vue js this is terrible way to do this
            //image.is_test_image ^= true
            //return image

        },
        toggleTestImageAll: function () {

            console.log("toggleTestImage")
            this.$http.post('/images/edit/toggle_test_image/all', {

                images: images_vue.Images
            })
                .then(function (response) {

                    console.log(response);
                    location.reload();

                })
                .catch(function (error) {
                    console.log(error);
                });


        },
        toggle_done_labeling: function (image) {


            this.$http.post('/images/edit/toggle_done_labeling', {

                image: image
            })
                .then(function (response) {

                    console.log(response);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        toggle_done_labeling_all: function () {

            this.$http.post('/images/edit/toggle_done_labeling_all', {

                images: images_vue.Images
            })
                .then(function (response) {

                    console.log(response);

                    images_vue.get_images()

                    setTimeout(function () {
                        annotate.mouse_move()
                    }, 500);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        remove_duplicate_filenames: function () {

            this.$http.post('/images/edit/remove_duplicate_filenames', {

                images: images_vue.Images
            })
                .then(function (response) {

                    console.log(response);

                    images_vue.get_images()

                    setTimeout(function () {
                        annotate.mouse_move()
                    }, 500);

                })
                .catch(function (error) {
                    console.log(error);
                });

        },
        test_placeholder: function () {


        },
        imageDelete: function (image) {

            console.log("Deleting image")
            this.$http.post('/images/delete', {

                image: image

            })
                .then(function (response) {

                    console.log(response);

                })
                .catch(function (error) {
                    console.log(error);
                });
            images_vue.get_images()

            setTimeout(function () {
                annotate.mouse_move()
            }, 500);
            setTimeout(function () {
                annotate.mouse_move()
            }, 1000);
            setTimeout(function () {
                annotate.mouse_move()
            }, 2000);
        }
    }
})


// TODO better way ....
setTimeout(function () {
    annotate.get_boxes()
}, 3000);

setTimeout(function () {
    annotate.mouse_move()
}, 3100);

setTimeout(function () {
    annotate.mouse_move()
}, 5000);
