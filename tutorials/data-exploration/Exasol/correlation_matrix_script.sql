open schema util;

CREATE OR REPLACE SCRIPT corr_matrix(src_schema, src_table, trg_schema, trg_table, sub_matrix_dimension, output_sql) as
        
        /*
        NOTE:
                if the source table/view contains columns that are not numerical, create a view with numerical columns of interest
        */
                
        /*
        general structure of the script
        1. define and execute initial sql statements
                1.1 get column names
                1.2 get the necessary combinations to calculate the correlation matrix and devide it into submatrices with dimensionalty defined in the input parameters 
                1.3 generate sql to generate sqls that contains all the expressions for the column combinations of each submatrix
                1.4 generate sql to generate the target ddl statement
        2. sending the queries for each submatrix to the db and saving the results in an array structure [id of submatrix][position in submatrix]
        3. changin the the format from submtraix array structre to correlation matrix outout structure
        4. generate insert statement into the target table
        */
        if sub_matrix_dimension > 100 then
                sub_matrix_dimension = 100
        end
        
        
        /*
        1.1 get column names
        */
        sql_cols = [[
select  column_name c
from    exa_all_columns
where   column_schema = ']] .. src_schema .. [['
and     column_table = ']] .. src_table .. [['
order   by column_ordinal_position
        ]]
        
        
        /*
        1.2 get the necessary combinations to calculate the correlation matrix and devide it into submatrices with dimensionalty defined in the input parameters
        
        array_position - position of the combination in the overall set
        sub_matrix_id - id of the submtraix
        sub_matrix_position - position in the submtraix
        */ 
        sql_cols_xy = [[
with b as (
        select  column_name c, column_ordinal_position p
        from    exa_all_columns
        where   column_schema = ']] .. src_schema .. [['
        and     column_table = ']] .. src_table .. [['
)
select  x_col, x_pos, 
        y_col, y_pos, 
        array_position, sub_matrix_id, 
        row_number() over(partition by sub_matrix_id order by x_pos, y_pos) sub_matrix_position
from (
        select  x.c x_col, x.p x_pos, 
                y.c y_col, y.p y_pos, 
                row_number() over(order by x.p, y.p) array_position, 
                dense_rank() over(order by ceil(x.p/]] .. sub_matrix_dimension .. [[), ceil(y.p/]] .. sub_matrix_dimension .. [[)) sub_matrix_id
        from    b x, b y
        where   x.p < y.p
        order   by local.sub_matrix_id, local.array_position
)
        ]]
        
        /*
        1.3 generate sql to generate sqls that contains all the expressions for the column combinations of each submatrix
        */
        sql_corr_sql = [[
with b as (
        select  column_name c, column_ordinal_position p
        from    exa_all_columns
        where   column_schema = ']] .. src_schema .. [['
        and     column_table = ']] .. src_table .. [['
)
select sub_matrix_id, 'select ' || listagg('corr("' || x_col || '", "' || y_col || '")', ', ') within group(order by array_position)  || ' from "]] .. src_schema .. [["."]] .. src_table .. [["' sql_text
from (
        select  x.c x_col, x.p x_pos, 
                y.c y_col, y.p y_pos, 
                row_number() over(order by x.p, y.p) array_position,
                dense_rank() over(order by ceil(x.p/]] .. sub_matrix_dimension .. [[), ceil(y.p/]] .. sub_matrix_dimension .. [[)) sub_matrix_id
        from    b x, b y
        where   x.p < y.p
) 
group by sub_matrix_id
order by sub_matrix_id
        ]]
        
        
        /*
        1.4 generate sql to generate the target ddl statement
        */
        sql_trg_ddl_sql = [[
select  'create or replace table "]] .. trg_schema .. [["."]] .. trg_table.. [[" (ord int, col_name varchar(255), ' || listagg('"' || column_name || '" double', ', ') within group(order by column_ordinal_position) || ')' sql_target_ddl
from    exa_all_columns
where   column_schema = ']] .. src_schema .. [['
and     column_table = ']] .. src_table .. [['
group   by column_schema, column_table        
        ]]
        
        
        
        
        if output_sql then
                output(sql_cols)
                output(sql_cols_xy)
                output(sql_corr_sql)
                output(sql_trg_ddl_sql)
        end
        
        query([[rollback]])
        cols = query(sql_cols)
        query([[commit]])
        cols_xy = query(sql_cols_xy)
        query([[commit]])
        corr_sql = query(sql_corr_sql)
        query([[commit]])
        sql_trg_ddl = query(sql_trg_ddl_sql)[1].SQL_TARGET_DDL
        query([[commit]])
        
        if output_sql then
                output(sql_trg_ddl)
                for i=1, #corr_sql, 1 do
                        output(corr_sql[i].SQL_TEXT)
                end
        end
        
        
        
        /*
        2. sending the queries for each submatrix to the db and saving the results in aa array structure [id of submatrix][position in submatrix]
        */
        corr_array = {}
        for i=1, #corr_sql, 1 do
                corr_array[i] = {}
                res = query(corr_sql[i].SQL_TEXT)
                for j=1, #res[1], 1 do
                        table.insert(corr_array[i], res[1][j])
                end
        end
        
        
        /*
        3. changin the the format from submtraix array structre to correlation matrix outout structure
        */
        corr_matrix = {}
        for x=1, #cols, 1 do
                corr_matrix[cols[x].C] = {}
                for y=1, #cols, 1 do
                        corr_matrix[cols[x].C][cols[y].C] = [[null]]
                end
        end
        
        for r=1, #cols_xy, 1 do
                corr_matrix[cols_xy[r].X_COL][cols_xy[r].Y_COL] = corr_array[cols_xy[r].SUB_MATRIX_ID][cols_xy[r].SUB_MATRIX_POSITION]
                corr_matrix[cols_xy[r].Y_COL][cols_xy[r].X_COL] = corr_matrix[cols_xy[r].X_COL][cols_xy[r].Y_COL]
        end
        

        /*
        4. generate insert statement into the target table
        */
        col_list = [[ord, col_name]]
        val_list = [[]]
        for y=1, #cols, 1 do
                col_list = col_list .. [[, "]] .. cols[y].C .. [["]]
                val_list = val_list .. [[(]] .. y .. [[, ']] .. cols[y].C .. [[']]
                for x=1, #cols, 1 do
                        val_list = val_list .. [[, ]] .. corr_matrix[cols[x].C][cols[y].C]
                end
                val_list = val_list .. [[)]]
                if y < #cols then
                        val_list = val_list .. [[, ]]
                end
        end
        sql_trg_dml = [[insert into "]] .. trg_schema .. [["."]] .. trg_table .. [["(]] .. col_list .. [[) values ]] .. val_list
        
        if output_sql then
                output(sql_trg_ddl)
                output(sql_trg_dml)
        end
        
        query(sql_trg_ddl)
        query([[commit]])
        query(sql_trg_dml)
        query([[commit]])
;


create or replace table "corr T%est" as
with    ten as (
select  level n 
from    dual 
connect by level <= 10 
order   by false
)
select  
random(460, 3422) "C+ 1",
random(712, 4794) "C+ 2",
random(29, 1189)  "C+ 3",
random(666, 3068) "C+ 4",
random(947, 4023) "C+ 5",
random(658, 4083) "C+ 6",
random(803, 3335) "C+ 7",
random(240, 1294) "C+ 8",
random(967, 1066) "C+ 9",
random(148, 1601) "C+ 10",
random(270, 1258) "C+ 11",
random(222, 1768) "C+ 12",
random(682, 3167) "C+ 13",
random(708, 4187) "C+ 14",
random(330, 4651) "C+ 15",
random(943, 1489) "C+ 16",
random(335, 4433) "C+ 17",
random(542, 2440) "C+ 18",
random(364, 1328) "C+ 19",
random(908, 3115) "C+ 20",
random(334, 1343) "C+ 21",
random(80, 1969)  "C+ 22",
random(87, 4643)  "C+ 23",
random(872, 2224) "C+ 24",
random(772, 1118) "C+ 25",
random(988, 1504) "C+ 26",
random(15, 4304)  "C+ 27",
random(843, 4122) "C+ 28",
random(28, 2152)  "C+ 29",
random(105, 4077) "C+ 30",
random(119, 3750) "C+ 31",
random(549, 3475) "C+ 32",
random(224, 4918) "C+ 33",
random(762, 4296) "C+ 34",
random(651, 1570) "C+ 35",
random(331, 4023) "C+ 36",
random(235, 1351) "C+ 37",
random(393, 4000) "C+ 38",
random(235, 3144) "C+ 39",
random(503, 3149) "C+ 40",
random(849, 1619) "C+ 41",
random(360, 1307) "C+ 42",
random(249, 3868) "C+ 43",
random(250, 4111) "C+ 44",
random(857, 1146) "C+ 45",
random(7, 2126)   "C+ 46",
random(987, 2717) "C+ 47",
random(1, 4004)   "C+ 48",
random(623, 4306) "C+ 49",
random(35, 2885)  "C+ 50",
random(280, 4010) "C+ 51",
random(214, 1487) "C+ 52",
random(113, 2047) "C+ 53",
random(311, 2183) "C+ 54",
random(238, 1927) "C+ 55",
random(484, 2585) "C+ 56",
random(71, 2027)  "C+ 57",
random(757, 4603) "C+ 58",
random(18, 2482)  "C+ 59",
random(715, 2212) "C+ 60",
random(316, 4819) "C+ 61",
random(14, 2054)  "C+ 62",
random(748, 2808) "C+ 63",
random(476, 3975) "C+ 64",
random(684, 3920) "C+ 65",
random(712, 2072) "C+ 66",
random(514, 4336) "C+ 67",
random(163, 4783) "C+ 68",
random(251, 3596) "C+ 69",
random(926, 2467) "C+ 70",
random(871, 4298) "C+ 71",
random(192, 4924) "C+ 72",
random(110, 3430) "C+ 73",
random(483, 3271) "C+ 74",
random(55, 4024)  "C+ 75",
random(204, 3730) "C+ 76",
random(490, 3150) "C+ 77",
random(765, 4228) "C+ 78",
random(460, 2066) "C+ 79",
random(620, 1471) "C+ 80",
random(643, 4448) "C+ 81",
random(490, 4347) "C+ 82",
random(381, 4397) "C+ 83",
random(730, 3561) "C+ 84",
random(893, 3936) "C+ 85",
random(284, 1861) "C+ 86",
random(41, 1656)  "C+ 87",
random(576, 4093) "C+ 88",
random(188, 3932) "C+ 89",
random(410, 4893) "C+ 90",
random(802, 4774) "C+ 91",
random(752, 2232) "C+ 92",
random(594, 3682) "C+ 93",
random(387, 3044) "C+ 94",
random(601, 4759) "C+ 95",
random(836, 1961) "C+ 96",
random(264, 2761) "C+ 97",
random(944, 2203) "C+ 98",
random(620, 2454) "C+ 99",
random(674, 1160) "C+ 100"
from    ten, ten, ten, ten, ten, ten
;



execute script corr_matrix('UTIL', 'corr T%est', 'UTIL', 'CORR  r3s', 20, true) with output;
select * from "CORR  r3s";