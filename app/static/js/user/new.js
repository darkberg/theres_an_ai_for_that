

class user {
	constructor () {
		this.id = null,
		this.name = null,
		this.email = null,
		this.password = null,
		this.verify = null,
		this.error_username = null,
		this.error_password = null,
		this.error_verify = null,
        this.error_email = null,
        this.code = null
	}
}

user_ = new user;

var user_new = new Vue({
	el: "#new_user",
	mounted: function(event) {

		Vue.prototype.$http = axios;

	},
	created: function () {
		
	},
	destroyed: function() {
	
	},

	data: {
		user: user_
	},

	methods: {
		user_new_function: function(event) {
			
			console.log("New user")
			this.$http.post('/user/new', {
				user: this.user
			})
			.then(function (response) {
			
			console.log(response);

			user_new.user.error_password = response.data['error_password'];
			user_new.user.error_verify = response.data['error_verify'];
            user_new.user.error_email = response.data['error_email'];
            user_new.user.error_code = response.data['error_code'];

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