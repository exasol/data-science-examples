open schema util;

CREATE OR REPLACE SCRIPT table_stats(src_schema, src_table, trg_schema, trg_table, output_sql) as
        
        /*
        general structure of the script
        1. generate sql to retrieve column information
        2. use column information to create a lua table 
                2.1 different calculations per column depending on the data type
                2.3 in some cases an addtional subselect is needed
        3. genertate a select statement with all the expressions for the statistics
                3.1 transpose the result set to have the statistics in one column
        4. generate the ddl for the output table 
        5. generate an insert statement
        */
        
        /*
        1. generate sql to retrieve column information
        */
        query([[rollback]]) --rollback in case of a readlock
        col_list_sql = [[
select  column_schema, column_table, column_name, column_ordinal_position, column_type,
        case    when    substr(column_type, 0, 7) = 'DECIMAL'   then 'DECIMAL' 
                when    substr(column_type, 0, 9) = 'TIMESTAMP' then 'TIMESTAMP' 
                when    substr(column_type, 0, 4) = 'CHAR'      then 'CHAR'
                when    substr(column_type, 0, 7) = 'VARCHAR'   then 'VARCHAR'
                else    column_type
        end column_type_generic,
        upper(regexp_replace(column_name, '([^a-zA-Z0-9])', '_')) column_name_norm     
from    exa_user_columns
where   column_schema = ']] .. src_schema .. [['
and     column_table = ']] .. src_table .. [['
order   by column_ordinal_position
        ]]
        
        --output(col_list_sql)
        col_list = query(col_list_sql)
        query([[commit]])
        
        --variables containing the column names of the col_list result set
        cs = [[COLUMN_SCHEMA]]
        ct = [[COLUMN_TABLE]]
        cn = [[COLUMN_NAME]]
        cnn = [[COLUMN_NAME_NORM]]
        cop = [[COLUMN_ORDINAL_POSITION]]
        ctp = [[COLUMN_TYPE]]
        ctg = [[COLUMN_TYPE_GENERIC]]
        sed = [[SQL_EXPRESSION_DESCRIPTION]] 
        se = [[SQL_EXPRESSION]]
        sf = [[SQL_FROM]]
        ser = [[SQL_EXPRESSION_RESULT]]
        
        --helper function 
        function add_to_trg_out()
                expr_num = expr_num + 1
                trg_out[expr_num] = {}
                trg_out[expr_num][cs] = col_list[rid][cs]
                trg_out[expr_num][ct] = col_list[rid][ct]
                trg_out[expr_num][cn] = col_list[rid][cn]
                trg_out[expr_num][cnn] = col_list[rid][cnn]
                trg_out[expr_num][cop] = col_list[rid][cop]
                trg_out[expr_num][ctp] = col_list[rid][ctp]
                trg_out[expr_num][ctg] = col_list[rid][ctg]
        end
        
        trg_out = {}
        expr_num = 1
        rid = 0
        --count(*) works with every table
        trg_out[expr_num] = {}
        trg_out[expr_num][cs] =  src_schema
        trg_out[expr_num][ct] =  src_table
        trg_out[expr_num][cn] = [[null]]
        trg_out[expr_num][cn] = [[null]]
        trg_out[expr_num][cop] = 0
        trg_out[expr_num][ctp] = [[null]]
        trg_out[expr_num][ctg] = [[null]]
        trg_out[expr_num][sed] = [[the number of records in the source table]]
        trg_out[expr_num][se] = string.format([[count(*) CNT]], src_table)
        trg_out[expr_num][sf] = [[]] --workaround for nil/null values
        
        
        /*
        2. use column information to create a lua table
        */
        for r=1, #col_list, 1 do
                rid = r
                r_st = [["]] .. col_list[r][cs] .. [["."]] .. col_list[r][ct] .. [["]]
                r_tc = [["]] .. col_list[r][ct] .. [["."]] .. col_list[r][cn] .. [["]]
                r_c = [["]] .. col_list[r][cn] .. [["]]
                r_cn = col_list[r][cnn]
                
                add_to_trg_out()
                trg_out[expr_num][sed] = [[the number of null values]]
                trg_out[expr_num][se] = string.format([[coalesce(sum(case when %s is null then 1 end), 0) CNT_NULL_%s]],
                                                                               r_tc,                               r_cn)
                trg_out[expr_num][sf] = [[]]
                
                if col_list[r][ctg] == [[BOOLEAN]] then 
                        --tf_ratio
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the ratio between true and false values]]
                        trg_out[expr_num][se] = string.format([[coalesce(sum(case when %s then 1 end) / sum(case when not %s then 1 end), 0) TF_RATIO_%s]], r_tc, r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                end
                
                if col_list[r][ctg] ~= [[BOOLEAN]] and col_list[r][ctg] ~= [[GEOMETRY]] then
                        --cnt_dist 
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the number of distinct values]]
                        trg_out[expr_num][se] = string.format([[coalesce(count(distinct(%s)), 0) CNT_DIST_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                end
                
                /*
                2.1 different calculations per column depending on the data 
                */
                if col_list[r][ctg] == [[DECIMAL]] or col_list[r][ctg] == [[DOUBLE]] then
                        --min
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the minimum value]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(min(%s)), 'null')  MIN_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                        
                        --pct25
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the value of the 0.25 percentile]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(percentile_cont(0.25) within group(order by %s)), 'null') PCT25_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                        
                        --avg
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the avergage value]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(avg(%s)), 'null') AVG_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                        
                        
                        --med
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the median value]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(median(%s)), 'null') MED_%s]], r_tc,  r_cn)
                        trg_out[expr_num][sf] = [[]]
                        
                        --pct75
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the value of the 0.75 percentile]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(percentile_cont(0.75) within group(order by %s)), 'null') PCT75_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                        
                        --max
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the maximum value]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(max(%s)), 'null') MAX_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                        
                        --stddev
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the standard deviation]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(stddev(%s)), 'null') STDDEV_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]         
                        
                end
                
                if col_list[r][ctg] == [[DATE]] or col_list[r][ctg] == [[TIMESTAMP]] then
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the minimum value]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(min(%s)), 'null') MIN_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                        
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the maximum value]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(max(%s)), 'null') MAX_%s]], r_tc, r_cn)
                        trg_out[expr_num][sf] = [[]]
                end
                
                if col_list[r][ctg] == [[CHAR]] or col_list[r][ctg] == [[VARCHAR]] then
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the value(s) with the most occurences]]
                        trg_out[expr_num][se] = string.format([[coalesce(first_value(C_%s.TOP_%s), 'null') TOP_%s]], r_cn, r_cn ,r_cn)
                        
                        /*
                        2.3 in some cases an addtional subselect is needed
                        */                                                               
                        --qualify only from version 7 onwards                                                              
                        trg_out[expr_num][sf] = string.format([[(select listagg(distinct %s, '; ' on overflow truncate with count) within group(order by %s) as TOP_%s, count(*) as OCC_%s from %s group by %s qualify OCC_%s = max(OCC_%s) over()) as C_%s]], r_c, r_c, r_cn, r_cn, r_st, r_c, r_cn, r_cn, r_cn)          
                                                                                                                                        
                        add_to_trg_out()
                        trg_out[expr_num][sed] = [[the number of most occurences]]
                        trg_out[expr_num][se] = string.format([[coalesce(to_char(first_value(C_%s.OCC_%s)), 'null') OCC_%s]], r_cn, r_cn, r_cn)
                        trg_out[expr_num][sf] = [[]]
                end
                
        end
        
        col_list = nil
        
        /*
        3. genertate a select statement with all the expressions for the statistics
        */
        trg_select_list = [[select ]]
        trg_from_list = string.format([[from "%s"."%s" as "%s"]], src_schema, src_table, src_table)
        
        
        /*
        3.1 transpose the result set to have the statistics in one column
        */
        for i=1, #trg_out, 1 do
                if i ~= 1 then
                        trg_select_list = trg_select_list .. [[, ]]
                end
                trg_select_list = trg_select_list .. trg_out[i][se]
                
                if trg_out[i][sf] ~= [[]] then
                        trg_from_list = trg_from_list .. [[, ]] .. trg_out[i][sf]
                end
        end
        
        trg_select = trg_select_list .. [[ ]] .. trg_from_list
        
        if output_sql then
                output(trg_select)
        end
        
        trg_select_res = query(trg_select)[1]
        query([[commit]])


        /*
        4. generate the ddl for the output table 
        */
        trg_ddl = string.format([[create or replace table "%s"."%s"( ID int, %s varchar(255), %s varchar(255), %s varchar(255), %s int, %s varchar(255), %s varchar(1000), %s varchar(2000))]], trg_schema, trg_table, cs, ct, cn, cop, ctp, sed, ser)
                                                
        if output_sql then
                output(trg_ddl)
        end
        
        query(trg_ddl)
        query([[commit]])
        
        
        /*
        5. generate an insert statement
        */
        trg_dml = string.format([[insert into "%s"."%s"(ID, %s, %s, %s, %s, %s, %s, %s) values]], trg_schema, trg_table, cs, ct, cn, cop, ctp, sed, ser)
        for i=1, #trg_out, 1 do
                trg_out[i][ser] = trg_select_res[i]
                
                if i ~= 1 then
                        trg_dml = trg_dml .. [[, ]]
                end
                trg_dml = trg_dml .. string.format([[(%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s')]], 
                                        i, 
                                        trg_out[i][cs], 
                                        trg_out[i][ct], 
                                        trg_out[i][cn], 
                                        trg_out[i][cop], 
                                        trg_out[i][ctp], 
                                        trg_out[i][sed], 
                                        trg_out[i][ser])
             
        end
        if output_sql then
                output(trg_dml)
        end
        query(trg_dml)
        query([[commit]])
        trg_dml = nil
;

create or replace table "dt Test" (
"N um" number,
"D cm" decimal(5, 0),
"F lo" float,
"D bl" double, 
"D at" date,
"T im" timestamp,
"B ol" boolean,
"I ym" INTERVAL YEAR (3) TO MONTH,
"I ds" INTERVAL DAY (3) TO SECOND (6),
"G eo" GEOMETRY,
"V ch" varchar(200),
"C ha" char(200)	
)
;

insert into "dt Test"("N um", "D cm", "F lo", "D bl", "D at", "T im", "B ol", "V ch", "C ha")
select  random() num,
        level dcm,
        random() flo,
        random() dbl,
        current_date - level dat,
        add_seconds(current_timestamp, -trunc(random(0,86400))) tim,
        random()>0.7 bol,
        chr(trunc(random(0,25)+65)) vch,
        chr(trunc(random(0,25)+65)) cha
from dual
connect by level <= 1000;


execute script table_stats('UTIL', 'dt Test', 'UTIL', 'DT_TEST_RES', true) with output;
select * from "dt Test"; 
select * from DT_TEST_RES;