class image_ {
    constructor() {
        this.id = null,
        this.public_url = null,
        this.width = null,
        this.height = null,
        this.public_url_thumb = null
    }
}

var Images = [];
var current_image = new image_;

var test_vue = new Vue({
    el: "#test",
    mounted: function (event) {

    },
    created: function () {

        Vue.prototype.$http = axios
 
        console.log("Getting image ids")
        this.$http.get('/images/test/out', {
        })
            .then(function (response) {

                for (i in response.data.image_ids) {
                    var image = new image_;
                    image.id = response.data.image_ids[i];
                    image.width = response.data.width[i];
                    image.height = response.data.height[i];
                    image.public_url = response.data.public_url[i];
                    Images.push(image)
                }
                current_image.id = Images[0].id,
                current_image.width = Images[0].width,
                current_image.height = Images[0].height,
                current_image.public_url = Images[0].public_url


            })
            .catch(function (error) {
                console.log(error);
            });

        this.Loading = "";
        // TODO better way....
    },
    destroyed: function () {
    },

    data: {
        Images: Images
    },

    methods: {
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

            location.reload();
        }
    }
})


// TODO better way ....

setTimeout(function () {
    
}, 3000);

setTimeout(function () {
    
}, 5000);
