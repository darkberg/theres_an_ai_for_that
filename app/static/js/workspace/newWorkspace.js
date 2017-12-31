

class project {
	constructor () {
		this.id = null,
		this.name = null,
        this.user_id = null,
        this.user = null
	}
}


var project_object = new project;


var new_project = new Vue({
    el: "#new_project",
	mounted: function(event) {
	
		Vue.prototype.$http = axios

	},
	created: function () {
		
	},
	destroyed: function() {
		
	},

	data: {
        project: project_object
	},
	methods: {

		new_project_function: function(event) {

			console.log("Creating")
			this.$http.post('/project/new', {
  
			})
			.then(function (response) {
                console.log(response);

            if (response.data['success'] == true) {
                window.location.href = '/upload';
            }

			})
			.catch(function (error) {
			console.log(error);
			});
		}
	}
})