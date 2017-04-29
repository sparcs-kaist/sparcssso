var first_call_g = true;

/*
s_date_g: start date, manually
e_date_g: date of today
*/
var s_date_g = "2016-08-16"
var e_date_g = (new Date()).toISOString().substring(0, 10);
var service_g = "all"

$('.input-daterange').datepicker({
    autoclose: true,
    todayHighlight: true,
    format: "yyyy-mm-dd",    
});

$(document).ready(function(){
    $('.nav-tabs a:first').tab('show')
    set_date_to_calendar(s_date_g, e_date_g);
    get_stats(service_g, s_date_g, e_date_g);
    find_dropdown_menu_pos();
});

$(window).resize(function(){
    find_dropdown_menu_pos();        
});

$("body").on("click", ".dropdown-service", function(){
    service_g = $(this).text();
    change_service(service_g);   
});

$(".btn-get-stat").click(function(){
    s_date_g = $(".s-date").val();
    e_date_g = $(".e-date").val();
    chart_storage.length = 0
    get_stats(service_g, s_date_g, e_date_g);
});

$(".nav-tabs").click(function(){
    setTimeout(function(){
        reflow_chart();
    }, 0);
});

$(window).resize(function(){
    for(var i = 0; i < chart_storage.length; i++){
        var ch = chart_storage[i];
        if(ch.legend.options.borderColor == "#CCD"){
            ch.legend.update(get_legend_option("kaist-department"))
        }
    }
})

var atomic_list_g = ["kaist-professor", "kaist-employee"]

/**
jquery ajax call
@param - read https://wiki.sparcs.org/w/index.php/SPARCS_SSO_API_%EB%AA%85%EC%84%B8
 */
function get_stats(client_ids, date_from, date_to){
    var param = {};
    var arg_names = ["client_ids", "date_from", "date_to"];
    for(var idx = 0; idx < arguments.length; idx++){
        param[arg_names[idx]] = arguments[idx];
    }
    $.ajax({
        url: "/api/v2/stats/",
        data: param,
        success: success_stats,
        dataType: "Json",
    });
}


/**
jquery ajax success function
 */
function success_stats(data, textStatus, jqXHR){
    
    /* Add up all fields to "all" key */
    append_data_of_all(data);

    var service_list = get_services(data);
    var s_data = get_data_of_s(data, "all");
    change_service("all");
    
    if(Object.keys(s_data).length != 0){
        var property_arr = get_properties(s_data);
        var property_kaist_arr = get_properties_kaist(s_data);
        var formatted_data = get_formatted_data(s_data);
        for(var idx = 0; idx < property_arr.length; idx++){
            var property = property_arr[idx];
            
            if(property != "kaist"){ 
                var f_data = formatted_data[property];
                draw_graph(formatted_data[property], property);
            } else{
                for(var kaidx in property_kaist_arr){
                    var property_kaist = property_kaist_arr[kaidx]
                    var f_data = formatted_data[property][property_kaist];
                    draw_graph_kaist(f_data, property, property_kaist);
                }
            }
        }
    } else {
        if(!first_call_g){
            alert("선택한 구간의 데이터가 없습니다!");
        }
    }
    
    /* only first call, add services to dropdown */
    if(first_call_g){
        add_services(service_list);
        first_call_g = false;
        destroy_not_auth_chart(s_data);
    }
}

/* Append "all" as key to stats.
   It is statstics of sum of all services*/
function append_data_of_all(data) {
    var stats = data["stats"]
    stats_all = {
        "alias": "all",
        "data": {},
    };
    $.each(stats, function(service, s_obj){
        sum_or_copy(s_obj["data"], stats_all["data"]);
    })
    stats["all"] = stats_all;
}

/* Copy object-tree from original_root to new_root.
   If new_root has already have some number-leaf,
   just add original_root's value . */
function sum_or_copy(original_root, new_root) {
    $.each(original_root, function(k, v){
        if(typeof(v) == "number"){
            new_root[k] = new_root[k] + v || v;
            return;
        }
        if(!is_key(new_root, k)){
            new_root[k] = {};
        }
        sum_or_copy(v, new_root[k]);
    })
    return new_root;
}

function change_service(s_name){
    $(".s-name").text(s_name);
}


/**
Graph drawing function
*/
var chart_storage = []

function draw_graph(f_data, property) {
    
    /* professor, employee */
    if(is_emt_of_arr(atomic_list_g, property)){
        var x = f_data["series"][0]["data"].pop()
        var property = property.replace("_", "-");
        $("#"+property+"-cell").text(x);
        return 0;
    }

    var property = property.replace("_", "-");
    
    var t_chart_option = get_t_chart_option(property, f_data);
    var t_c = Highcharts.chart(property + "-t-chart", t_chart_option);
    chart_storage.push(t_c)

    var r_chart_option = get_r_chart_option(property, f_data);
    var r_c = Highcharts.chart(property + "-r-chart", r_chart_option);
    chart_storage.push(r_c)
}

function draw_graph_kaist(f_data, property, property_2nd){
    var property_class = [property, property_2nd].join("-");
    property_class = property_class.replace("_", "-")
    draw_graph(f_data, property_class);
}

function reflow_chart(){
    for(var i = 0; i < chart_storage.length; i++){
        var ch = chart_storage[i];
        ch.reflow();
    }
}

function get_legend_option(property) {
    var w = $(".chart-body").width();
    if(property == "kaist-department"){
        return {
            borderColor: '#CCD',
            borderWidth: 1,
            itemWidth: w,
            maxHeight: 150
        }
    } else if (w < 550){
        return {
            borderColor: '#CCC',
            borderWidth: 1,
            itemWidth: 100,
            maxHeight: 100
        }
    } else {
        return {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            y: 30,
            borderColor: '#CCC',
            borderWidth: 1,
        }
    }

}

function get_column_base_option(property, f_data){
    return {
        chart: {
            type: 'column'
        },
        title: {
            text: property
        },
        xAxis: {
            categories: f_data["xAxis"]["categories"]
        },
        yAxis: {
            min: 0,
            title: {
                text: null
            },
            stackLabels: {
                enabled: true,
                style: {
                    fontWeight: 'bold',
                    color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
                }
            }
        },
        legend: get_legend_option(property),
        tooltip: {
            headerFormat: '<b>{point.x}</b><br/>',
            pointFormat: '{series.name}: {point.y}'
        },
    }
}

function get_t_chart_option(property, f_data){
    var base_option = get_column_base_option(property, f_data)
    base_option["plotOptions"] = {
        column: {
            stacking: 'normal',
        }
    }
    base_option["series"] = f_data["series"]
    return base_option
}

function get_r_chart_option(property, f_data){
    // recent chart only need last data as array
    var base_option = get_column_base_option(property, f_data)
    if(property != "kaist-department"){
        var categories = base_option["xAxis"]["categories"];
        base_option["xAxis"]["categories"] = [categories[categories.length - 1]];
        base_option["series"] = $.map(f_data["series"], function(v, i){
            v = $.extend({}, v);
            v_data = v["data"] // Array
            v["data"] = [v_data[v_data.length - 1],];
            return v
        })
        
    } else{

        base_option["chart"]["type"] = "pie"
        base_option["series"] = [{
            "name": "department",
            "data": $.map(f_data["series"], function(v, i){
                v = $.extend({}, v);
                v_data = v["data"];
                return {
                    "name": v["name"],
                    "y": v_data[v_data.length - 1]
                }
            }).sort(function (a, b) {
                return b.y - a.y
            })
        }]
        base_option["plotOptions"] = {
            pie: {
                dataLabels: {
                    enabled: false,
                }
            }
        },
        base_option["tooltip"] = {
            pointFormat: '<b>{point.percentage:.1f}%</b>'
        },
        delete base_option["xAxis"]
        delete base_option["yAxis"]
    }
    return base_option
}


/**
Stats object manipulation function
*/

/**
@param {obj} data - json object from stats api
@returns {array} - array of services
*/
function get_services(data){
    var stats = data["stats"];
    return Object.keys(stats);
}

function get_data_of_s(data, s_name){
    if(typeof(s_name) == "undefined"){
        return {};
    } else{
        return data["stats"][s_name]["data"];
    }
}

function get_properties(s_data){
    var date_arr = Object.keys(s_data);
    return Object.keys(s_data[date_arr[date_arr.length -1]]);
}

function get_properties_kaist(s_data) {
    var date_arr = Object.keys(s_data);
    return Object.keys(s_data[date_arr[date_arr.length -1]]["kaist"]);
}

/*
@param {obj} s_data - Data format
{
    2016-08-17T12:46:56+00:00: {
        account: {
            all: int_all,
            email: int_email,
            ...
        },
    },
    2016-08-18T12:55:35+00:00: {
        ...
    },
}

@return {obj} - Data format
{
    <property>: {
        series: [
            {
                name: "label1",
                data: [y1, y2, y3]
            },
            {
                name: "label2",
                data: [y1, y2, y3]
            }
        ],
        xAxis: {
            categories: ['x1', 'x2', 'x3']
        },
    },
    kaist: {
        2nd_property: {
            series: [...],
            xAxis: {...}
        },
        department: {
            series: [
                {
                    name: <name>,
                    y: <y>
                },
            ]
        }
    }   
}
*/

function get_formatted_data(s_data){
    
    function simplify_date(s_data){
        for(let d in s_data){
           rename_key(s_data, d, d.split("+")[0]);
        }
    }

    function get_date_arr(){
        return Object.keys(s_data).sort();
    }

    function get_properties(){
        var date_arr = Object.keys(s_data);
        return Object.keys(s_data[date_arr[date_arr.length -1]]);
    }

    function get_properties_kaist() {
        var date_arr = Object.keys(s_data);
        return Object.keys(s_data[date_arr[date_arr.length -1]]["kaist"]);
    }

    function build_space(date_arr, properties_arr, properties_kaist_arr){
        var formatted_obj = {};
        for(var idx = 0; idx < properties_arr.length; idx++){
            p = properties_arr[idx];
            if(p != "kaist"){
                formatted_obj = set_emt_to_obj(formatted_obj, [p, "series"], {});
                formatted_obj = set_emt_to_obj(formatted_obj, [p, "xAxis", "categories"], date_arr);
            }
        }
        for(var idx = 0; idx < properties_kaist_arr.length; idx++){
            pk = properties_kaist_arr[idx];
            formatted_obj = set_emt_to_obj(formatted_obj, ["kaist", pk, "series"], {});
            formatted_obj = set_emt_to_obj(formatted_obj, ["kaist", pk, "xAxis", "categories"], date_arr);
        }
        return formatted_obj;
    }
    
    var num_of_bar = Math.ceil($(".chart-body").width() / 50);
    simplify_date(s_data);
    reduce_data(s_data, num_of_bar);
    var date_arr = get_date_arr();
    var properties_arr = get_properties();
    var properties_kaist_arr = get_properties_kaist();
    var formatted_obj = build_space(date_arr, properties_arr, properties_kaist_arr);
    
    for(var idx = 0; idx < date_arr.length; idx++){
        var date_key = date_arr[idx];
        var attr_obj = s_data[date_key];

        for(var property in attr_obj){
            if(property != "kaist"){
                preprocess_data(attr_obj, property);
                for(var label in attr_obj[property]){
                    if(!is_valid_key_arr(formatted_obj, [property, "series", label])){
                        formatted_obj[property]["series"][label] = {
                            "name": label,
                            "data": []
                        }
                    }
                    formatted_obj[property]["series"][label]["data"].push(attr_obj[property][label]);
                }
            } else{ /* kaist case */
                for(var property_2nd in attr_obj[property]){
                    var attr_2nd_obj = attr_obj[property];
                    
                    preprocess_data(attr_obj, property, property_2nd);

                    if(is_emt_of_arr(atomic_list_g, property+"-"+property_2nd)){
                        var atom = attr_2nd_obj[property_2nd];
                        attr_2nd_obj[property_2nd] = [atom];
                    }
                    
                    for(var label in attr_2nd_obj[property_2nd]){
                        if(!is_valid_key_arr(formatted_obj, [property, property_2nd, "series", label])){
                            formatted_obj[property][property_2nd]["series"][label] = {
                                "name": label,
                                "data": []
                            }
                        }
                        formatted_obj[property][property_2nd]["series"][label]["data"].push(attr_obj[property][property_2nd][label]);
                    }           
                }
            }
        }
    }

    for(var p in formatted_obj){
        if(p != "kaist"){
            formatted_obj[p]["series"] = make_formatted_to_arr(formatted_obj[p]["series"]);
        } else {
            for(var pk in formatted_obj[p]){
                formatted_obj[p][pk]["series"] = make_formatted_to_arr(formatted_obj[p][pk]["series"]);
            }
        }
    }
    return formatted_obj;
}

/*
There's bottle neck at drawing chart which has
many bars. And label of bar need enough space.
So, system should select part of data.

Heuristic methodologically, #bar = (width of chart) / 40

window_size = Math.ceil(#s_data /(#bar - 1))
e.g.) #bar = 4, #s_data = 10
window_size = ceil(10/(4-1)) = 3
0 1 2 3 4 5 6 7 8 9
s     s     s     s
*/
function reduce_data(s_data, num){
    var key_arr = Object.keys(s_data);
    var window_size = Math.ceil(key_arr.length/(num - 1));
    for(var idx in key_arr){
        if(idx % window_size != 0){
            delete s_data[key_arr[idx]];
        }
    }
}

/*
manipulate formatted_obj for purpose
- birth_year: append {year: 0} which api does not contain for spacing

@return: r_values
*/
function preprocess_data(attr_obj, property, property_2nd) {
    
    var p_attr_obj = attr_obj[property];
    
    switch(property){
        case "account":
            delete p_attr_obj["all"];
            break;
        case "birth_year":
            p_attr_obj = preprocess_data_birth_year(p_attr_obj);
            break;
        case "kaist":
            p_attr_obj = preprocess_data_kaist(p_attr_obj, property_2nd);
            break;
    }
    
}

/**
@param {obj} p_attr_obj - apijson["birth_year"]
- append {year: 0} which api does not contain for spacing
- compatible to preprocess_data_kaist
*/
function preprocess_data_birth_year(p_attr_obj){
    date_arr = Object.keys(p_attr_obj);
    min_date = min(date_arr);
    max_date = max(date_arr);
    for(var d = min_date; d <= max_date; d++){
        if(date_arr.indexOf(d+"") === -1){
            p_attr_obj[d] = 0;
        }
    }
    return p_attr_obj;
}

/**
parsing json["kaist"] to 2nd-depth
@param {obj} p_attr_obj - apijson["kaist"]
@param {string} property_2nd - birth_year, department, employee, gender, professor, start_year
@return preprocessed p_attr_obj;
*/
function preprocess_data_kaist(p_attr_obj, property_2nd){
    var p2nd_attr_obj = p_attr_obj[property_2nd];
    switch(property_2nd){
        case "birth_year":
            preprocess_data_birth_year(p2nd_attr_obj);
            break;
        case "department":
            preprocess_data_dept(p2nd_attr_obj);
            break;
    }
}

/*
@param {obj} p_attr_obj
- change department code to name
*/
function preprocess_data_dept(p_attr_obj) {
    for(var code in p_attr_obj){
        if(is_key(dept_data, code)){
            rename_key(p_attr_obj, code, dept_data[code]);
        } else {
            rename_key(p_attr_obj, code, "uk-"+code);
        }
    }
}

/**
DOM manipulation function with jquery
*/
function add_services(services){
    for(let s of services){
        if(!s.startsWith("test")){
            $("#service-dropdown-menu").append(
                '<li id=dropdown-' + s + ' class="dropdown-service"  ><a href="#">' + s + '</a></li>'
            );
        }
    }
}

function find_dropdown_menu_pos(){
    $dm_left = $("#service-dropdown").position();
    $("#service-dropdown-menu").css("left", $dm_left.left);
}

function set_date_to_calendar(s_date, e_date){
    $(".s-date").val(s_date);
    $(".e-date").val(e_date);
}

function destroy_not_auth_chart(s_data){
    var len = Object.keys(s_data).length;
    if(len == 0){
        $(".chart-lv-1").remove();
        $(".chart-lv-2").remove();
    } else if (len < 3){
        $(".chart-lv-2").remove();
    }
}


/*
Help function
*/
function min(x) {
    var value;
    for (var i = 0; i < x.length; i++) {
        if (value === undefined || x[i] < value) {
            value = x[i];
        }
    }
    if (value === undefined) {
        return NaN;
    }
    return value;
}

function max(x) {
    var value;
    for (var i = 0; i < x.length; i++) {
        if (value === undefined || x[i] > value) {
            value = x[i];
        }
    }
    if (value === undefined) {
        return NaN;
    }
    return value;
}

function is_valid_key_arr(obj, key_arr){
    for(var idx in key_arr){
        var key = key_arr[idx];
        if(Object.keys(obj).indexOf(key) != -1){
            var obj = obj[key];
        } else {
            return false;
        }
    }
    return true;
}

/*
@return obj = {
    x: {
        y: value
    }
} when key_arr is [x, y]
*/
function set_emt_to_obj(obj, key_arr, value){
    var copied_obj = JSON.parse(JSON.stringify(obj));  
    if(key_arr.length == 1){
        var key = key_arr[0];
        copied_obj[key] = value;
    } else {
        var key = key_arr.shift();
        if(!is_key(copied_obj, key)){
            copied_obj[key] = {};
        }
        var new_obj = copied_obj[key]; 
        copied_obj[key] = set_emt_to_obj(new_obj, key_arr, value);
    }
    return copied_obj;
}

function is_key(obj, key){
    return (Object.keys(obj).indexOf(key+"") != -1);
}

function rename_key(obj, o_k, n_k) {
    Object.defineProperty(
        obj,
        n_k,
        Object.getOwnPropertyDescriptor(
            obj,
            o_k
    ));
    delete obj[o_k];
}


function is_emt_of_arr(arr, obj) {
    return (arr.indexOf(obj) != -1);
}

function make_formatted_to_arr(formatted_obj){
    var r_arr = [];
    for(var label in formatted_obj){
        r_arr.push(formatted_obj[label]);
    }
    return r_arr;
}

/* global data */
var dept_data = {
    0: 'Undecided',
    3648: 'Bio and Brain Engineering',
    132: 'Biological Sciences',
    2222: 'Biomedical Science and Engineering Program',
    936: 'Business',
    33: 'Capstone Design',
    451: 'Chemical and Biomolecular Engineering',
    150: 'Chemistry',
    441: 'Civil and Environmental Engineering',
    4419: 'Departmemt of Aerospace Engineering',
    4418: 'Departmemt of Mechanical Engineering',
    331: 'Department of Industrial Systems Engineering',
    151: 'Department of Mathematical Sciences',
    3992: 'Division of Future Vehicle',
    4201: 'Economics Program',
    4431: 'Entrepreneurship Program',
    4305: 'Executive MBA',
    4398: 'Finance Executive MBA',
    4303: 'Finance MBA',
    3919: 'Financial Engineering Program',
    4310: 'Financial Engineering Program',
    973: 'General Required',
    3941: 'Global Information &amp; Telecommunication Technology Program',
    4200: 'Graduate Program for Future Strategy',
    3539: 'Graduate School of Culture Technology',
    4144: 'Graduate School of Information Security',
    4438: 'Graduate School of Innovation & Technology Management',
    4549: 'Graduate School of Knowledge Service Engineering',
    3605: 'Graduate School of Medical Science and Engineering',
    3990: 'Graduate School of Science and Technology Policy',
    4422: 'Graduate School of Web Science Technology',
    3799: 'Graduate school of EEWS',
    3692: 'Graduate school of Nanoscience &amp; Technology',
    4493: 'Green Business and Policy Program',
    340: 'Industrial Design',
    4312: 'Information Management Program',
    3723: 'Information and Communications Engineering',
    4306: 'Information and Media MBA',
    3978: 'Intellectual Property Minor Program for Undergradu',
    3920: 'Master of Science Journalism',
    3882: 'Master of intellectual property',
    421: 'Materials Science and Engineering',
    4141: 'Minor Program in Culture Technology',
    3993: 'Minor Program in Science and Technology Policy',
    4425: 'Moon Soul Graduate School of Future Strategy',
    221: 'Nuclear and Quantum Engineering',
    110: 'Physics',
    2410: 'Polymer Science and Engineering Program',
    4182: 'Professional MBA',
    4427: 'Program of Brain and Cognitive Engineering',
    4547: 'School of Business and Technology Management',
    4548: 'School of Business and Technology Management',
    4421: 'School of Computing',
    4423: 'School of Electrical Engineering',
    4424: 'School of Humanities &amp; Social Sciences',
    4301: 'School of Management Engineering',
    4183: 'Social Entrepreneurship MBA',
    3703: 'Software Graduate Program',
    3701: 'Space Exploration Engineering Program',
    4307: 'Techno-MBA',
    3997: 'The Cho Chun Shik Graduate School for Green Transportation',
    3520: 'The Robotics Program',
    4: 'Undergraduate Research Participation',
};

